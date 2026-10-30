const { test, expect } = require('@playwright/test')

const pokemonList = { results: [
  { name: 'bulbasaur', url: 'https://pokeapi.co/api/v2/pokemon/1/' },
  { name: 'ivysaur', url: 'https://pokeapi.co/api/v2/pokemon/2/' },
  { name: 'venusaur', url: 'https://pokeapi.co/api/v2/pokemon/3/' }
] }

const ivysaur = {
  types: [{ slot: 1, type: { name: 'grass' } }],
  stats: [{ stat: { name: 'hp' }, base_stat: 60 }],
  abilities: [
    { is_hidden: false, ability: { name: 'overgrow' } },
    { is_hidden: true, ability: { name: 'chlorophyll' } }
  ],
  sprites: { front_default: null }
}

test.beforeEach(async ({ page }) => {
  await page.route('https://pokeapi.co/api/v2/pokemon/?limit=50', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(pokemonList) }))
  await page.route('https://pokeapi.co/api/v2/pokemon/ivysaur', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ivysaur) }))
})

test('front page lists ivysaur and the trademark notice', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('ivysaur')).toBeVisible()
  await expect(page.getByText('Pokémon and Pokémon character names are trademarks of Nintendo.')).toBeVisible()
})

test('ivysaur navigation shows hidden ability and correct neighbors', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('link', { name: 'ivysaur' }).click()
  await expect(page).toHaveURL(/\/pokemon\/ivysaur$/)
  await expect(page.getByText('chlorophyll')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Previous' })).toHaveAttribute('href', '/pokemon/bulbasaur')
  await expect(page.getByRole('link', { name: 'Next' })).toHaveAttribute('href', '/pokemon/venusaur')
})
