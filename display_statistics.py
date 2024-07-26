from terminaltables import AsciiTable


def display_statistics_working(information_vacancies: dict, source_name: str) -> None:
    """Выводит в таблице, статистику запрашиваемых вакансий с сайта SuperJob.

    Args:
        information_vacancies (dict): Статистика по запрашиваемой вакансии
    """
    table_data = [['Наименование вакансий', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    
    for language_name, info_vacancy in information_vacancies.items():
        table_data.append([language_name, *info_vacancy.values()])
    
    fished_table = AsciiTable(table_data, title=source_name)
    
    print(fished_table.table)