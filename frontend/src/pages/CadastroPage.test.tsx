import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CadastroContent } from './CadastroPage';
import { desocupacaoFixture, imovelFixture } from '../test/fixtures';
import { renderWithRouter } from '../test/render';

const apiServiceMock = vi.hoisted(() => ({
  createDesocupacao: vi.fn(),
  createImovel: vi.fn(),
  listDesocupacoes: vi.fn(),
  listImoveis: vi.fn(),
  exportXlsx: vi.fn(),
  removeDesocupacao: vi.fn(),
}));

vi.mock('../services/api', () => ({
  apiService: apiServiceMock,
}));

async function fillDesocupacaoForm(user: ReturnType<typeof userEvent.setup>) {
  await user.selectOptions(screen.getByLabelText(/Imovel cadastrado/), imovelFixture.idImovel);
  await user.selectOptions(screen.getByLabelText(/Status do Evento/), 'Desocupacao');
  await user.type(screen.getByLabelText(/Data do Evento/), '2025-07-03');
  await user.type(screen.getByLabelText(/Data de Inicio do Contrato/), '2023-10-24');
  await user.type(screen.getByLabelText(/Valor do Aluguel/), '2500.5');
  await user.type(screen.getByLabelText(/Dias de Vacancia/), '12');
  await user.type(screen.getByLabelText(/Mes/), '7');
  await user.type(screen.getByLabelText(/Ano/), '2025');
  await user.type(screen.getByLabelText(/Motivo da Desocupacao/), 'Mudou de estado');
}

describe('CadastroContent', () => {
  beforeEach(() => {
    Object.values(apiServiceMock).forEach((mock) => mock.mockReset());
    apiServiceMock.listDesocupacoes.mockResolvedValue([]);
    apiServiceMock.listImoveis.mockResolvedValue([]);
  });

  it('loads an empty list and blocks invalid submit', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CadastroContent />);

    expect(await screen.findByText('Nenhum registro ainda. Cadastre o primeiro acima.')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Salvar' }));

    expect(await screen.findAllByText(/Obrigat|Informe|M/)).not.toHaveLength(0);
    expect(apiServiceMock.createDesocupacao).not.toHaveBeenCalled();
  });

  it('creates a desocupacao, resets the form and refreshes the latest list', async () => {
    const user = userEvent.setup();
    apiServiceMock.listDesocupacoes.mockResolvedValueOnce([]).mockResolvedValueOnce([desocupacaoFixture]);
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    apiServiceMock.createDesocupacao.mockResolvedValue(desocupacaoFixture);
    renderWithRouter(<CadastroContent />);
    await screen.findByText('Nenhum registro ainda. Cadastre o primeiro acima.');

    await fillDesocupacaoForm(user);
    await user.click(screen.getByRole('button', { name: 'Salvar' }));

    expect(await screen.findByText('Desocupacao cadastrada.')).toBeInTheDocument();
    expect(await screen.findByText('Plaza Mediterraneo')).toBeInTheDocument();
    expect(apiServiceMock.createDesocupacao).toHaveBeenCalledWith(
      expect.objectContaining({
        idImovel: imovelFixture.idImovel,
        cidade: imovelFixture.cidade,
        edificio: imovelFixture.edificio,
        numeroApto: imovelFixture.numeroApto,
        mes: 7,
        ano: 2025,
      }),
    );
    expect(screen.getByLabelText(/Cidade/)).toHaveValue('');
  });

  it('shows create and initial load errors', async () => {
    const user = userEvent.setup();
    apiServiceMock.listDesocupacoes.mockRejectedValueOnce(new Error('Falha ao carregar'));
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    apiServiceMock.createDesocupacao.mockRejectedValueOnce(new Error('Falha ao cadastrar'));
    renderWithRouter(<CadastroContent />);

    expect(await screen.findByText('Falha ao carregar')).toBeInTheDocument();
    await fillDesocupacaoForm(user);
    await user.click(screen.getByRole('button', { name: 'Salvar' }));

    expect(await screen.findByText('Falha ao cadastrar')).toBeInTheDocument();
  });

  it('exports by creating and clicking a download link', async () => {
    const user = userEvent.setup();
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    apiServiceMock.exportXlsx.mockResolvedValue({ url: 'https://signed', filename: 'desocupacoes.xlsx' });
    renderWithRouter(<CadastroContent />);
    await screen.findByText('Nenhum registro ainda. Cadastre o primeiro acima.');

    await user.click(screen.getByRole('button', { name: /Exportar/ }));

    expect(apiServiceMock.exportXlsx).toHaveBeenCalledOnce();
    expect(click).toHaveBeenCalledOnce();
  });

  it('removes only after confirmation and refreshes on success', async () => {
    const user = userEvent.setup();
    apiServiceMock.listDesocupacoes
      .mockResolvedValueOnce([desocupacaoFixture])
      .mockResolvedValueOnce([desocupacaoFixture])
      .mockResolvedValueOnce([]);
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    apiServiceMock.removeDesocupacao.mockResolvedValue({ id: desocupacaoFixture.id, status: 'DELETED' });
    const confirm = vi.spyOn(window, 'confirm');
    renderWithRouter(<CadastroContent />);
    await screen.findByText('Plaza Mediterraneo');

    confirm.mockReturnValueOnce(false);
    await user.click(screen.getByRole('button', { name: 'Remover' }));
    expect(apiServiceMock.removeDesocupacao).not.toHaveBeenCalled();

    confirm.mockReturnValueOnce(true);
    await user.click(screen.getByRole('button', { name: 'Remover' }));

    expect(await screen.findByText('Desocupacao removida.')).toBeInTheDocument();
    expect(apiServiceMock.removeDesocupacao).toHaveBeenCalledWith('desoc-1', '2025-07-03');
  });

  it('shows remove errors and clears the removing state', async () => {
    const user = userEvent.setup();
    apiServiceMock.listDesocupacoes.mockResolvedValue([desocupacaoFixture]);
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    apiServiceMock.removeDesocupacao.mockRejectedValue(new Error('Falha ao remover'));
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderWithRouter(<CadastroContent />);
    await screen.findByText('Plaza Mediterraneo');

    await user.click(screen.getByRole('button', { name: 'Remover' }));

    expect(await screen.findByText('Falha ao remover')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Remover' })).toBeEnabled());
  });
});
