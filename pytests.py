import pytest
import os
import tempfile
from datetime import datetime, timedelta
from app import database, models
from unittest.mock import patch, Mock
from app import extractors

@pytest.fixture
def temp_db():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    try:
        db = database.Database(db_path)
        db.create_tables()
        yield db
    finally:
        os.close(fd)
        os.remove(db_path)

def test_insert_and_retrieve_article(temp_db):
    article = models.Article(
        article_id="test123",
        url="http://testurl.com/1",
        title="Breaking News",
        summary="Lead summary.",
        published=datetime(2025, 7, 24, 13, 30, 0),
        source="skift",
        author="Reporter"
    )
    assert temp_db.insert_article(article) is True
    result = temp_db.get_article_by_id("test123")
    assert result is not None
    assert result.title == "Breaking News"
    assert result.source == "skift"





def skift_html():
    # Minimal HTML sample for Skift extraction
    return '''
    <article>
        <a href="http://skift.com/articleX">Title X</a>
        <time datetime="2025-07-24T07:00:00Z"></time>
        <p>Summary X</p>
    </article>
    '''



@patch('app.extractors.requests.get')
def test_skift_extractor_success(mock_get):
    mock_get.return_value = Mock(status_code=200, text=skift_html())
    articles = extractors.fetch_skift_articles()
    assert len(articles) == 1
    art = articles[0]
    assert art.title == "Title X"
    assert art.url == "http://skift.com/articleX"
    assert art.summary == "Summary X"


def phocuswire_html():
    # Minimal HTML sample for PhocusWire extraction
    return '''
    <div class="news-container">
        <a href="http://phocuswire.com/articleY">Title Y</a>
        <time datetime="2025-07-24T06:30:00Z"></time>
        <div class="summary">Summary Y</div>
    </div>
    '''

@patch('app.extractors.requests.get')
def test_phocuswire_extractor_success(mock_get):
    mock_get.return_value = Mock(status_code=200, text=phocuswire_html())
    articles = extractors.fetch_phocuswire_articles()
    assert len(articles) == 1
    art = articles[0]
    assert art.title == "Title Y"
    assert art.url == "http://phocuswire.com/articleY"
    assert art.summary == "Summary Y"

