import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CadastroImoveisContent } from './CadastroImoveisPage';
import { imovelFixture } from '../test/fixtures';
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

async function fillImovelForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/Cidade/), ' florianópolis ');
  await user.type(screen.getByLabelText(/Edificio/), ' plaza   mediterrâneo ');
  await user.type(screen.getByLabelText(/Numero do apto/), '326');
  await user.type(screen.getByLabelText(/Area privativa/), '72.5');
  await user.selectOptions(screen.getByLabelText(/Tipologia/), '2Q');
}

describe('CadastroImoveisContent', () => {
  beforeEach(() => {
    Object.values(apiServiceMock).forEach((mock) => mock.mockReset());
    apiServiceMock.listImoveis.mockResolvedValue([]);
  });

  it('loads empty state and blocks invalid submit', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CadastroImoveisContent />);

    expect(await screen.findByText('Nenhum imovel ainda. Cadastre o primeiro acima.')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Salvar' }));

    expect(await screen.findAllByText(/Obrig|Informe|Minimo/)).not.toHaveLength(0);
    expect(apiServiceMock.createImovel).not.toHaveBeenCalled();
  });

  it('normalizes input, creates imovel and refreshes table', async () => {
    const user = userEvent.setup();
    apiServiceMock.listImoveis.mockResolvedValueOnce([]).mockResolvedValueOnce([imovelFixture]);
    apiServiceMock.createImovel.mockResolvedValue(imovelFixture);
    renderWithRouter(<CadastroImoveisContent />);
    await screen.findByText('Nenhum imovel ainda. Cadastre o primeiro acima.');

    await fillImovelForm(user);
    await user.click(screen.getByRole('button', { name: 'Salvar' }));

    expect(await screen.findByText(`Imovel ${imovelFixture.idImovel} cadastrado.`)).toBeInTheDocument();
    expect(apiServiceMock.createImovel).toHaveBeenCalledWith(
      expect.objectContaining({
        cidade: 'Florianopolis',
        edificio: 'Plaza Mediterraneo',
        numeroApto: '326',
      }),
    );
    expect(await screen.findByText('Plaza Mediterraneo')).toBeInTheDocument();
  });

  it('shows load and duplicate errors', async () => {
    const user = userEvent.setup();
    apiServiceMock.listImoveis.mockRejectedValueOnce(new Error('Falha ao carregar lista'));
    apiServiceMock.createImovel.mockRejectedValueOnce(new Error('Este imovel ja foi cadastrado.'));
    renderWithRouter(<CadastroImoveisContent />);

    expect(await screen.findByText('Falha ao carregar lista')).toBeInTheDocument();
    await fillImovelForm(user);
    await user.click(screen.getByRole('button', { name: 'Salvar' }));

    expect(await screen.findByText('Este imovel ja foi cadastrado.')).toBeInTheDocument();
  });

  it('renders existing imoveis with formatted numeric values and truncated id title', async () => {
    apiServiceMock.listImoveis.mockResolvedValue([imovelFixture]);
    renderWithRouter(<CadastroImoveisContent />);

    expect(await screen.findByText('Plaza Mediterraneo')).toBeInTheDocument();
    expect(screen.getByText('72.50')).toBeInTheDocument();
    expect(screen.getByTitle(imovelFixture.idImovel)).toBeInTheDocument();
  });
});
