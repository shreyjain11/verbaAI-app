
install:
	pip install -r requirements.txt

start:
	streamlit run run.py

test:
	pytest
