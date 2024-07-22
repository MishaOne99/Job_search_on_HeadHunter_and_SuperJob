'''Выводит в таблице, статистику запрашиваемых вакансий с HeadHunter и SuperJob'''


import os
import argparse
from dotenv import load_dotenv
from requests import get
from terminaltables import AsciiTable


def predict_rub_salary_for_HeadHunter(list_vacancies_by_page: list) -> list[int]:
    """Модуль предназначен, чтобы найти приблизительную заработной плату, указанную в вакансии с HeadHunter.

    Args:
        list_vacancies_by_page (list): Получает список вакансий n-го количества страниц 

    Returns:
        list[int]: Возвращает список, с приблизительной зарабатной платой
    """
    salary_vacancy = []

    for list_vacancies in list_vacancies_by_page:
        for vacancy in list_vacancies:
            
            salary = vacancy['salary']

            if salary is None:
                continue
            if salary['currency'] != 'RUR':
                continue

            payment_from = salary['from'] if salary['from'] != None else 0
            payment_to = salary['to'] if salary['to'] != None else 0
            
            average_salary = predict_salary(payment_from, payment_to)
            salary_vacancy.append(average_salary)

    return salary_vacancy


def predict_rub_salary_for_SuperJob(list_vacancies: list) -> list[int]:
    """Модуль предназначен, чтобы найти приблизительную заработной плату, указанную в вакансии с SuperJob.

    Args:
        list_vacancies (list): Получает список вакансий

    Returns:
        list[int]: Возвращает список, с приблизительной зарабатной платой
    """
    salary_vacancy = []
    
    for vacancy in list_vacancies:
        payment_from = vacancy['payment_from']
        payment_to = vacancy['payment_to']
        currency = vacancy['currency']
        
        if (payment_from == 0 and payment_to == 0) or currency != 'rub':
            continue
        average_salary = predict_salary(payment_from, payment_to)
        salary_vacancy.append(average_salary)
    
    return salary_vacancy


def predict_salary(salary_from: int, salary_to: int) -> int:
    """Вычисляет приблизительную заработную плату.

    Args:
        salary_from (int): Заработная плата, от
        salary_to (int): Заработная плата, до

    Returns:
        int: Приблизительная заработная плата
    """
    if salary_from != 0 and salary_from != 0:
        return((salary_from + salary_to) / 2)
    if salary_to == 0:
        return(salary_from * 1.2)
    if salary_from == 0:
        return(salary_to * 0.8)


def displaying_job_statistics_from_SuperJob(information_vacancies: dict) -> None:
    """Выводит в таблице, статистику запрашиваемых вакансий с сайта SuperJob.

    Args:
        information_vacancies (dict): Статистика по запрашиваемой вакансии
    """
    table_data = [['Наименование вакансий', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    
    for language_name, info_vacancy in information_vacancies.items():
        table_data.append([language_name, *info_vacancy.values()])
    
    fished_table = AsciiTable(table_data, 'SuperJob MOSCOW')
    
    print(fished_table.table)


def displaying_job_statistics_from_HeadHunter(information_vacancies: dict) -> None:
    """Выводит в таблице, статистику запрашиваемых вакансий с сайта HeadHunter.

    Args:
        information_vacancies (dict): Статистика по запрашиваемой вакансии
    """
    table_data = [['Наименование вакансии', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    
    for language_name, info_vacancy in information_vacancies.items():
        table_data.append([language_name, *info_vacancy.values()])
    
    fished_table = AsciiTable(table_data, 'HeadHunter MOSCOW')
    
    print(fished_table.table)


def collecting_job_statistics_from_HeadHunter(vacanсies: list[str]) -> dict:
    """Сбор статистики запрашиваемых вакансий с сайта HeadHunter.

    Args:
        vacancies (list[str]): Запрашиваемые вакансии

    Returns:
        dict: Статистика запрашиваемых вакансий
    """
    info_vacancy = {}

    for vacancy in vacanсies:
        list_vacancies = []

        page = 0
        pages_number = 5

        while page < pages_number:
            payload = payload = {'text': vacancy, 'area': 1, 'enable_snippets': 'true', 'page': page, 'per_page': 100}

            page_response = get('https://api.hh.ru/vacancies', params=payload)
            page_response.raise_for_status()

            page_payload = page_response.json()
            list_vacancies.append(page_payload['items'])
            page += 1

        salary_vacancy = predict_rub_salary_for_HeadHunter(list_vacancies_by_page=list_vacancies)

        info_vacancy[vacancy] = {"vacancies_found":page_payload['found'],
                                 "vacancies_processed": len(salary_vacancy), 
                                 "average_salary": int(sum(salary_vacancy)/len(salary_vacancy)) if len(salary_vacancy) != 0 
                                                                                                else None}
    return info_vacancy


def collecting_job_statistics_from_SuperJob(vacanсies: list[str]) -> dict:
    """Сбор статистики запрашиваемых вакансий с сайта SuperJob.

    Args:
        vacancies (list[str]): Запрашиваемые вакансии

    Returns:
        dict: Статистика запрашиваемых вакансий
    """
    load_dotenv()
    secret_key = os.getenv('SECRET_KEY_SUPER_JOB')
    headers = {'X-Api-App-Id': secret_key}

    info_vacancy = {}

    for vacancy in vacanсies:
        payload = {'town': 4, 'keyword': vacancy}

        response = get('https://api.superjob.ru/2.0/vacancies/', headers=headers, params=payload)
        response.raise_for_status()
        
        salary_vacancy = predict_rub_salary_for_SuperJob(response.json()['objects'])
        
        info_vacancy[vacancy] = {"vacancies_found": len(response.json()['objects']),
                                "vacancies_processed": len(salary_vacancy), 
                                "average_salary": int(sum(salary_vacancy)/len(salary_vacancy)) if len(salary_vacancy) != 0 
                                                                                               else None}
    
    return info_vacancy


def runs_collecting_statistics(vacancies: list[str]) -> None:
    """Запускает модули по сбору статистики вакансий и выводит их в таблице

    Args:
        vacancies (list[str]): Запрашиваемые вакансии
    """
    displaying_job_statistics_from_HeadHunter(collecting_job_statistics_from_HeadHunter(vacancies))
    displaying_job_statistics_from_SuperJob(collecting_job_statistics_from_SuperJob(vacancies))


def main():
    """Позволяет работать из командной строки
    """
    parser = argparse.ArgumentParser(description= 'Shows job statistics from Headhunter and SuperJob')
    parser.add_argument('Vacancies', type=str, nargs='+', default='Программист', help='Enter a list of professions that you are interested in')
    args = parser.parse_args()

    runs_collecting_statistics(args.Vacancies)


if __name__ == '__main__':
    main()