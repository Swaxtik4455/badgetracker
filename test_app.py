import pytest
from analytics import classify_participant, process_results_dataframe

def test_classify_participant():
    assert classify_participant(10, "Verified")[0] == "Completed"
    assert classify_participant(9, "Verified")[0] == "Almost Completed"
    assert classify_participant(8, "Verified")[0] == "Almost Completed"
    assert classify_participant(5, "Verified")[0] == "Needs Attention"
    assert classify_participant(0, "Verified")[0] == "Not Started"
    assert classify_participant(5, "Private Profile")[0] == "Manual Verification"

def test_process_results_dataframe():
    sample_results = [
        {"url": "https://skills.google/1", "status": "Verified", "badge_count": 10, "error_msg": None},
        {"url": "https://skills.google/2", "status": "Verified", "badge_count": 8, "error_msg": None},
        {"url": "https://skills.google/3", "status": "Private Profile", "badge_count": 0, "error_msg": "Private"}
    ]
    df = process_results_dataframe(sample_results)
    assert len(df) == 3
    assert df.loc[0, "Campaign Status"] == "Completed"
    assert df.loc[1, "Badges Remaining"] == 2
    assert df.loc[2, "Campaign Status"] == "Manual Verification"