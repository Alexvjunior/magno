import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CadastroContent } from './CadastroPage';
import { imovelFixture, movimentacaoFixture } from '../test/fixtures';
import { renderWithRouter } from '../test/render';

const apiServiceMock = vi.hoisted(() => ({
  createMovimentacao: vi.fn(),
  createImovel: vi.fn(),
  listMovimentacoes: vi.fn(),
  listImoveis: vi.fn(),
  exportXlsx: vi.fn(),
  removeMovimentacao: vi.fn(),
  removeImovel: vi.fn(),
}));

vi.mock('../services/api', () => ({
  apiService: apiServiceMock,
}));

async function fillMovimentacaoForm(user: ReturnType<typeof userEvent.setup>) {
  await user.selectOptions(screen.getByLabelText(/Imovel cadastrado/), imovelFixture.idImovel);
  await user.selectOptions(screen.getByLabelText(/Status do Evento/), 'Desocupacao');
  await user.type(screen.getByLabelText(/Data do Evento/), '2025-07-03');
  await user.type(screen.getByLabelText(/Data de Inicio do Contrato/), '2023-10-24');
  await user.type(screen.getByLabelText(/Mes/), '7');
  await user.type(screen.getByLabelText(/Ano/), '2025');
  await user.selectOptions(screen.getByLabelText(/Motivo da Desocupacao/), 'Mudança geográfica');
}

describe('CadastroContent', () => {
  beforeEach(() => {
    Object.values(apiServiceMock).forEach((mock) => mock.mockReset());
    apiServiceMock.listMovimentacoes.mockResolvedValue([]);
    apiServiceMock.listImoveis.mockResolvedValue([]);
  });

  it('loads an empty list and blocks invalid submit', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CadastroContent />);

    expect(await screen.findByText('Nenhum registro ainda. Cadastre o primeiro acima.')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Salvar' }));

    expect(await screen.findAllByText(/Obrigat|Informe|M/)).not.toHaveLength(0);
    expect(apiServiceMock.createMovimentacao).not.toHaveBeenCalled();
  });

  it('creates a movimentacao, resets the form and refreshes the latest list', async () => {
    const user = userEvent.setup();
    apiServiceMock.listMovimentacoes.mockResolvedValueOnce([]).mockResolvedValueOnce([movimentacaoFixture]);
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    apiServiceMock.createMovimentacao.mockResolvedValue(movimentacaoFixture);
    renderWithRouter(<CadastroContent />);
    await screen.findByText('Nenhum registro ainda. Cadastre o primeiro acima.');

    await fillMovimentacaoForm(user);
    await user.click(screen.getByRole('button', { name: 'Salvar' }));

    expect(await screen.findByText('Movimentacao cadastrada.')).toBeInTheDocument();
    expect(await screen.findByText('Plaza Mediterraneo')).toBeInTheDocument();
    expect(apiServiceMock.createMovimentacao).toHaveBeenCalledWith(
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

  it('keeps conditional fields blocked until status evento is selected', async () => {
    const user = userEvent.setup();
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    renderWithRouter(<CadastroContent />);
    await screen.findByText('Nenhum registro ainda. Cadastre o primeiro acima.');

    await user.selectOptions(screen.getByLabelText(/Imovel cadastrado/), imovelFixture.idImovel);

    expect(screen.getByLabelText(/Data de Inicio do Contrato/)).toBeDisabled();
    expect(screen.getByLabelText(/Valor do Aluguel/)).toBeDisabled();
    expect(screen.getByLabelText(/Dias de Vacancia/)).toBeDisabled();
    expect(screen.getByLabelText(/Motivo da Desocupacao/)).toBeDisabled();
  });

  it('enables only desocupacao fields for Desocupacao status', async () => {
    const user = userEvent.setup();
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    renderWithRouter(<CadastroContent />);
    await screen.findByText('Nenhum registro ainda. Cadastre o primeiro acima.');

    await user.selectOptions(screen.getByLabelText(/Imovel cadastrado/), imovelFixture.idImovel);
    await user.selectOptions(screen.getByLabelText(/Status do Evento/), 'Desocupacao');

    expect(screen.getByLabelText(/Data de Inicio do Contrato/)).toBeEnabled();
    expect(screen.getByLabelText(/Motivo da Desocupacao/)).toBeEnabled();
    expect(screen.getByLabelText(/Valor do Aluguel/)).toBeDisabled();
    expect(screen.getByLabelText(/Dias de Vacancia/)).toBeDisabled();
  });

  it('enables only locacao fields and clears desocupacao fields for Locacao status', async () => {
    const user = userEvent.setup();
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    renderWithRouter(<CadastroContent />);
    await screen.findByText('Nenhum registro ainda. Cadastre o primeiro acima.');

    await user.selectOptions(screen.getByLabelText(/Imovel cadastrado/), imovelFixture.idImovel);
    await user.selectOptions(screen.getByLabelText(/Status do Evento/), 'Desocupacao');
    await user.type(screen.getByLabelText(/Data de Inicio do Contrato/), '2023-10-24');
    await user.selectOptions(screen.getByLabelText(/Motivo da Desocupacao/), 'Mudança geográfica');

    await user.selectOptions(screen.getByLabelText(/Status do Evento/), 'Locacao');

    expect(screen.getByLabelText(/Valor do Aluguel/)).toBeEnabled();
    expect(screen.getByLabelText(/Dias de Vacancia/)).toBeEnabled();
    expect(screen.getByLabelText(/Data de Inicio do Contrato/)).toBeDisabled();
    expect(screen.getByLabelText(/Data de Inicio do Contrato/)).toHaveValue('');
    expect(screen.getByLabelText(/Motivo da Desocupacao/)).toBeDisabled();
    expect(screen.getByLabelText(/Motivo da Desocupacao/)).toHaveValue('');
  });

  it('shows create and initial load errors', async () => {
    const user = userEvent.setup();
    apiServiceMock.listMovimentacoes.mockRejectedValueOnce(new Error('Falha ao carregar'));
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    apiServiceMock.createMovimentacao.mockRejectedValueOnce(new Error('Falha ao cadastrar'));
    renderWithRouter(<CadastroContent />);

    expect(await screen.findByText('Falha ao carregar')).toBeInTheDocument();
    await fillMovimentacaoForm(user);
    await user.click(screen.getByRole('button', { name: 'Salvar' }));

    expect(await screen.findByText('Falha ao cadastrar')).toBeInTheDocument();
  });

  it('exports by creating and clicking a download link', async () => {
    const user = userEvent.setup();
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    apiServiceMock.exportXlsx.mockResolvedValue({ url: 'https://signed', filename: 'movimentacoes.xlsx' });
    renderWithRouter(<CadastroContent />);
    await screen.findByText('Nenhum registro ainda. Cadastre o primeiro acima.');

    await user.click(screen.getByRole('button', { name: /Exportar/ }));

    expect(apiServiceMock.exportXlsx).toHaveBeenCalledOnce();
    expect(click).toHaveBeenCalledOnce();
  });

  it('removes only after confirmation and refreshes on success', async () => {
    const user = userEvent.setup();
    apiServiceMock.listMovimentacoes
      .mockResolvedValueOnce([movimentacaoFixture])
      .mockResolvedValueOnce([movimentacaoFixture])
      .mockResolvedValueOnce([]);
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    apiServiceMock.removeMovimentacao.mockResolvedValue({ id: movimentacaoFixture.id, status: 'DELETED' });
    const confirm = vi.spyOn(window, 'confirm');
    renderWithRouter(<CadastroContent />);
    await screen.findByText('Plaza Mediterraneo');

    confirm.mockReturnValueOnce(false);
    await user.click(screen.getByRole('button', { name: 'Remover' }));
    expect(apiServiceMock.removeMovimentacao).not.toHaveBeenCalled();

    confirm.mockReturnValueOnce(true);
    await user.click(screen.getByRole('button', { name: 'Remover' }));

    expect(await screen.findByText('Movimentacao removida.')).toBeInTheDocument();
    expect(apiServiceMock.removeMovimentacao).toHaveBeenCalledWith('mov-1', '2025-07-03');
  });

  it('shows remove errors and clears the removing state', async () => {
    const user = userEvent.setup();
    apiServiceMock.listMovimentacoes.mockResolvedValue([movimentacaoFixture]);
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    apiServiceMock.removeMovimentacao.mockRejectedValue(new Error('Falha ao remover'));
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderWithRouter(<CadastroContent />);
    await screen.findByText('Plaza Mediterraneo');

    await user.click(screen.getByRole('button', { name: 'Remover' }));

    expect(await screen.findByText('Falha ao remover')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Remover' })).toBeEnabled());
  });
});
