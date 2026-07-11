import re
import json
from typing import List, Optional
from ..models.project import Project


class KworkJSONParser:
    """Парсер для извлечения данных проектов из JavaScript переменных"""

    def parse_projects(self, html: str) -> List[Project]:
        """
        Извлекает проекты из window.stateData или других JS переменных
        """
        projects = []

        # Ищем JSON данные в <script> тегах
        script_pattern = r'window\.stateData\s*=\s*({.*?});'
        match = re.search(script_pattern, html, re.DOTALL)

        if not match:
            # Попробуем другие паттерны
            script_pattern = r'window\.__NUXT__\s*=\s*({.*?});'
            match = re.search(script_pattern, html, re.DOTALL)

        if not match:
            print("Не найдены JavaScript данные")
            return []

        try:
            json_str = match.group(1)
            data = json.loads(json_str)

            # Ищем проекты в разных местах структуры данных
            projects = self._extract_projects_from_data(data)

        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")
        except Exception as e:
            print(f"Ошибка извлечения проектов: {e}")

        return projects

    def _extract_projects_from_data(self, data: dict) -> List[Project]:
        """Извлекает проекты из parsed JSON структуры"""
        projects = []

        # Проверяем разные возможные расположения данных
        # Вариант 1: прямой список проектов
        if isinstance(data, dict):
            # Ищем ключи с проектами
            for key in ['wants', 'projects', 'items', 'data']:
                if key in data and isinstance(data[key], list):
                    projects.extend(self._parse_project_list(data[key]))

            # Ищем вложенные структуры
            for value in data.values():
                if isinstance(value, dict):
                    nested = self._extract_projects_from_data(value)
                    projects.extend(nested)

        return projects

    def _parse_project_list(self, items: list) -> List[Project]:
        """Парсит список проектов из JSON"""
        projects = []

        for item in items:
            if not isinstance(item, dict):
                continue

            try:
                # Извлекаем обязательные поля
                project_id = str(item.get('id') or item.get('project_id') or item.get('want_id', ''))
                title = item.get('title') or item.get('name', '')

                if not project_id or not title:
                    continue

                # URL проекта
                url = f"https://kwork.ru/projects/{project_id}"

                # Цена
                price = self._extract_price(item)

                # Описание
                description = item.get('description') or item.get('desc', '')
                if description and len(description) > 100:
                    description = description[:100] + '...'

                project = Project(
                    id=project_id,
                    title=title,
                    url=url,
                    price=price,
                    description=description
                )

                projects.append(project)

            except Exception as e:
                print(f"Ошибка парсинга проекта: {e}")
                continue

        return projects

    def _extract_price(self, item: dict) -> Optional[str]:
        """Извлекает цену из разных полей"""
        # Разные возможные названия полей с ценой
        price_fields = ['price', 'budget', 'price_limit', 'volume']

        for field in price_fields:
            if field in item and item[field]:
                price = item[field]
                if isinstance(price, (int, float)):
                    return f"{int(price)} ₽"
                elif isinstance(price, str):
                    return f"{price} ₽"

        return None
