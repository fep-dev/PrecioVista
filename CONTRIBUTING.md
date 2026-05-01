# Contributing to PrecioVista

Thanks for wanting to contribute. Here's how.

## Ways to contribute

- Add store chains for a country
- Add a new country with its provinces
- Fix a bug (open an issue first)
- Improve the UI or accessibility
- Translate error messages or UI strings
- Write tests

## Getting started

```bash
git clone https://github.com/YOUR_USERNAME/preciovista.git
cd preciovista
npx serve .
```

No build step. Edit and refresh.

## Project structure

- `js/data.js` — add countries, provinces, and store chains here
- `css/styles.css` — all styles, uses CSS variables
- `js/supabase.js` — all database queries
- `js/auth.js` — authentication modals
- `js/app.js` — shared utilities and page logic

## Adding a new country

1. Add the country object to `PAISES` in `js/data.js`
2. Add its store chains to `CADENAS`
3. Add the flag emoji and currency symbol
4. Open a PR with the changes

## Pull request rules

- Keep it focused — one thing per PR
- Test in a browser before submitting
- Don't add new external dependencies without discussion
- Comment in Spanish (the codebase is in Spanish)

## License

By contributing you agree your code is licensed under CC BY-NC-SA 4.0.

## Questions

Open an issue with the `question` label.
