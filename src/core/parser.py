import re
from bs4 import BeautifulSoup
from typing import List, Optional
from ..models.project import Project


class KworkParser:
    def __init__(self, selectors: dict):
        self.selectors = selectors

    def parse_projects(self, html: str) -> List[Project]:
        soup = BeautifulSoup(html, 'lxml')
        projects = []

        card_selector = self.selectors.get('card_container', '.want-card')
        cards = soup.select(card_selector)

        for card in cards:
            try:
                project = self._parse_single_card(card)
                if project and self._validate_project(project):
                    projects.append(project)
            except Exception as e:
                print(f"Ошибка парсинга карточки проекта: {e}")
                continue

        return projects

    def _parse_single_card(self, card: BeautifulSoup) -> Optional[Project]:
        title_link_selector = self.selectors.get('title_link', '.wants-card__header-title a')
        link = card.select_one(title_link_selector)

        if not link:
            return None

        url = link.get('href', '')
        if not url:
            return None

        if not url.startswith('http'):
            url = 'https://kwork.ru' + url

        title = link.get_text(strip=True)
        project_id = self._extract_project_id(url)

        if not project_id:
            return None

        price = self._extract_price(card)
        description = self._extract_description(card)

        return Project(
            id=project_id,
            title=title,
            url=url,
            price=price,
            description=description
        )

    def _extract_project_id(self, url: str) -> Optional[str]:
        match = re.search(r'/projects/(\d+)', url)
        return match.group(1) if match else None

    def _extract_price(self, card: BeautifulSoup) -> Optional[str]:
        price_selector = self.selectors.get('price', '.wants-card__price')
        price_elem = card.select_one(price_selector)

        if not price_elem:
            return None

        price_text = price_elem.get_text(strip=True)
        match = re.search(r'(\d[\d\s]*\d|\d+)', price_text)

        if match:
            price_value = match.group(1).replace(' ', '')
            return f"{price_value} ₽"

        return None

    def _extract_description(self, card: BeautifulSoup) -> Optional[str]:
        desc_selector = self.selectors.get('description', '.wants-card__description-text')
        desc_elem = card.select_one(desc_selector)

        if not desc_elem:
            return None

        desc_text = desc_elem.get_text(strip=True)
        return desc_text[:100] + '...' if len(desc_text) > 100 else desc_text

    def _validate_project(self, project: Project) -> bool:
        return bool(project.id and project.title and project.url)
