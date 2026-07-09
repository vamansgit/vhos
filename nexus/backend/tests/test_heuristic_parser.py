from app.services.nlp.heuristic_parser import HeuristicSourcingParser

parser = HeuristicSourcingParser()


def test_parses_quantity_price_destination_deadline():
    text = "I need 1,000 amber glass dropper bottles, 30ml, delivered to Mumbai in 3 weeks, budget under ₹15/unit."
    result = parser.parse(text)

    assert result.quantity == 1000
    assert result.target_price == 15.0
    assert result.destination == "Mumbai"
    assert result.deadline_days == 21
    assert result.category == "product"
    assert "Searching now" in result.confirmation_line


def test_detects_packaging_category():
    result = parser.parse("I need 500 custom mailer boxes with my logo")
    assert result.category == "packaging"
    assert result.quantity == 500


def test_detects_logistics_category():
    result = parser.parse("Find me a courier for pan-India COD deliveries")
    assert result.category == "logistics"


def test_handles_sparse_input_gracefully():
    result = parser.parse("suppliers for candles")
    assert result.category == "product"
    assert result.quantity is None
    assert result.target_price is None
