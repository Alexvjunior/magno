import { expect, test, type Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('/login');
  await page.getByLabel('E-mail').fill('user@example.com');
  await page.getByLabel('Senha').fill('password1');
  await page.getByRole('button', { name: 'Entrar' }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByText('user@example.com')).toBeVisible();
}

async function openCadastro(page: Page, name: 'Imoveis' | 'Movimentacoes') {
  await page.getByRole('button', { name: 'Cadastros' }).click();
  await page.getByRole('menuitem', { name }).click();
}

async function fillImovel(page: Page) {
  await page.getByLabel(/Cidade/).fill('florianópolis');
  await page.getByLabel(/Edificio/).fill('plaza mediterrâneo');
  await page.getByLabel(/Numero do apto/).fill('326');
  await page.getByLabel(/Area privativa/).fill('72.5');
  await page.getByLabel(/Tipologia/).selectOption('2Q');
}

async function fillMovimentacao(page: Page) {
  await page.getByLabel(/Imovel cadastrado/).selectOption('FLORIANOPOLIS|PLAZA MEDITERRANEO|326');
  await page.getByLabel(/Status do Evento/).selectOption('Desocupacao');
  await page.getByLabel(/Data do Evento/).fill('2025-07-03');
  await page.getByLabel(/Data de Inicio do Contrato/).fill('2023-10-24');
  await page.getByLabel(/Mes/).fill('7');
  await page.getByLabel(/Ano/).fill('2025');
  await page.getByLabel(/Motivo da Desocupacao/).selectOption('Mudança geográfica');
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
  });
});

test('redirects anonymous dashboard users to login', async ({ page }) => {
  await page.goto('/dashboard');

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole('heading', { name: 'Entrar' })).toBeVisible();
});

test('mock user can manage imoveis and movimentacoes', async ({ page }) => {
  await login(page);

  await openCadastro(page, 'Imoveis');
  await expect(page.getByRole('dialog', { name: 'Cadastro de imoveis' })).toBeVisible();
  await fillImovel(page);
  await page.getByRole('button', { name: 'Salvar' }).click();
  await expect(page.getByText('Imovel FLORIANOPOLIS|PLAZA MEDITERRANEO|326 cadastrado.')).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Plaza Mediterraneo', exact: true })).toBeVisible();

  await fillImovel(page);
  await page.getByRole('button', { name: 'Salvar' }).click();
  await expect(page.getByText('Este imovel ja foi cadastrado.')).toBeVisible();
  await page.getByRole('button', { name: 'Fechar' }).click();

  await openCadastro(page, 'Movimentacoes');
  await expect(page.getByRole('dialog', { name: 'Cadastro de movimentacoes' })).toBeVisible();
  await fillMovimentacao(page);
  await page.getByRole('button', { name: 'Salvar' }).click();
  await expect(page.getByText('Movimentacao cadastrada.')).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Plaza Mediterraneo', exact: true })).toBeVisible();

  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: /Exportar/ }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/^movimentacoes-\d{4}-\d{2}-\d{2}\.csv$/);

  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: 'Remover' }).click();
  await expect(page.getByText('Movimentacao removida.')).toBeVisible();
  await expect(page.getByText('Nenhum registro ainda. Cadastre o primeiro acima.')).toBeVisible();
});
