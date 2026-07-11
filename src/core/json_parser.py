import re
import json
import html
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

                # Декодируем HTML entities в заголовке
                if title:
                    title = html.unescape(title)

                if not project_id or not title:
                    continue

                # URL проекта
                url = f"https://kwork.ru/projects/{project_id}"

                # Цены
                # priceLimit - желаемый бюджет
                # possiblePriceLimit - допустимый бюджет (обычно в 3 раза больше)
                price = self._extract_price(item, 'priceLimit')
                price_limit = self._extract_price(item, 'possiblePriceLimit')

                # Описание (полное и короткое)
                full_description = item.get('description') or item.get('desc', '')
                # Декодируем HTML entities в описании
                if full_description:
                    full_description = html.unescape(full_description)
                description = full_description[:100] + '...' if len(full_description) > 100 else full_description

                # Информация о заказчике
                payer_username = None
                payer_stats = None
                if 'payer' in item and isinstance(item['payer'], dict):
                    payer = item['payer']
                    payer_username = payer.get('username', '')

                    # Собираем статистику
                    stats_parts = []
                    if 'wantCount' in payer:
                        stats_parts.append(f"Проектов: {payer['wantCount']}")
                    if 'hiredPercent' in payer:
                        stats_parts.append(f"Нанято: {payer['hiredPercent']}%")
                    payer_stats = ' | '.join(stats_parts) if stats_parts else None

                # Время и предложения
                time_left = item.get('timeLeftFormatted') or item.get('timeLeft', '')
                # kwork_count - это количество предложений (kwork = предложение на Kwork.ru)
                offers_count = item.get('kwork_count', 0)

                project = Project(
                    id=project_id,
                    title=title,
                    url=url,
                    price=price,
                    price_limit=price_limit,
                    description=description,
                    full_description=full_description,
                    payer_username=payer_username,
                    payer_stats=payer_stats,
                    time_left=time_left,
                    offers_count=offers_count
                )

                projects.append(project)

            except Exception as e:
                print(f"Ошибка парсинга проекта: {e}")
                continue

        return projects

    def _extract_price(self, item: dict, field_name: str) -> Optional[str]:
        """Извлекает цену из указанного поля с форматированием"""
        if field_name in item and item[field_name]:
            price = item[field_name]
            if isinstance(price, (int, float)):
                # Форматируем: 55000 -> "55 000 ₽"
                price_int = int(price)
                price_formatted = f"{price_int:,}".replace(',', ' ')
                return f"{price_formatted} ₽"
            elif isinstance(price, str):
                # Если строка, пытаемся преобразовать в число и отформатировать
                try:
                    price_float = float(price)
                    price_int = int(price_float)
                    price_formatted = f"{price_int:,}".replace(',', ' ')
                    return f"{price_formatted} ₽"
                except ValueError:
                    # Если не число, возвращаем как есть
                    return f"{price} ₽"
        return None
