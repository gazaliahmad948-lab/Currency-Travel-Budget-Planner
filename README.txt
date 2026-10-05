CURRENCY & TRAVEL BUDGET PLANNER

FILES
- main.py: Streamlit user interface
- models.py: CurrencyConverter, TripBudget, Expense, BudgetReport classes
- services.py: exchange rates, public holidays, country comparison, Gemini AI
- utils.py: validation, regular expressions, JSON/CSV file handling, formatting
- requirements.txt: required packages
- data/: local JSON and CSV records are created here automatically

SETUP
1. Open the project folder in VS Code.
2. Open the terminal in that folder.
3. Run: python -m pip install -r requirements.txt
4. Set GEMINI_API_KEY before using AI Advice. The app uses gemini-3.8-flash by default; you can change it with GEMINI_MODEL.
5. Run: streamlit run main.py

IMPORTANT
- Internet is required for exchange-rate, public-holiday, and Gemini features.
- The country comparison uses daily cost estimates entered by the user; it does not claim that those estimates are official cost-of-living data.
