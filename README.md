# RIZZK Calculator

RIZZK Calculator (pronounced "Rizz-k") — sharp, refined position-sizing for traders who think in probabilities and move with style.

Author: Fuaad Abdullah  
Contact: [GoblinOSRep@gmail.com](mailto:GoblinOSRep@gmail.com)

Default UI: Polished emoji mode is the default. Use the sidebar "🦇 mode (ASCII emoticons)" toggle to switch to the ASCII-emoticon experience.

## Live Demo

🚀 [Try the live demo here](https://rr-calculator-2tywogeksqdgr4hf4jzssm.streamlit.app/)

![RIZZK Calculator Screenshot](assets/rizzk-demo.svg)

## What this is

- 🦇, polished Streamlit app to compute position size, stop-loss impact, and profit targets. Built for traders who want clean numbers without the fluff.

## Who this is for

Day traders, students, and new traders who want disciplined risk sizing.

## This is not

Not a signal service. Not financial advice. Just math with taste.

## Key Features

- Position sizing from account size and risk %
- Long and short support
- 1:1 and 2:1 profit targets
- Downloadable CSV of results
- Calculation history stored in session
- Input validation and clear feedback
- Clean UI with charts and metrics

## Local Development

If you want to run locally:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Usage

Fill the inputs: account size, risk %, entry, stop. Hit Calculate. Export CSV if you want to log the trade.

## Suggested Demo Flow (30-60 sec)

1. **Show defaults & explain risk %**: "Here we have a $10K account risking 1% per trade - that's disciplined $100 risk per position."

2. **Flip from long to short**: "Watch how the calculator handles both directions - same $100 risk, but short position gives us 20 shares at $95 entry with $100 stop."

3. **Build history**: "Each calculation adds to session history - perfect for reviewing multiple trade ideas in one sitting."

4. **Download CSV**: "Export your trade plan as CSV for your journal or spreadsheet analysis."

## Testing

Run unit tests with pytest:

```bash
pip install -r requirements.txt
pytest test_risk_reward.py -v
```

All core calculation logic is thoroughly unit-tested with comprehensive edge case coverage, including extreme sanity checks with tiny accounts and microscopic risks to ensure safety-first reliability.

## Tech

- Python 3.11
- Streamlit
- Pandas
- Pytest (unit testing)

## Engineering Approach

Built with production-grade practices: comprehensive type hints, thorough unit testing with edge case coverage, modular architecture, and safety-first error handling. The core calculation logic is battle-tested against extreme scenarios to ensure reliability in high-stakes trading environments.

## Tone

RIZZK is designed to be direct and pragmatic — modern, confident, and professional with an edge.

## License

MIT
