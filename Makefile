.PHONY: all test app
all:
	python run_all.py
test:
	pytest -q
app:
	streamlit run app/app.py
