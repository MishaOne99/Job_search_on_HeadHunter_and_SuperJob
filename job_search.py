'''Выводит в таблице, статистику запрашиваемых вакансий с HeadHunter и SuperJob'''


import os
import argparse
from dotenv import load_dotenv
from requests import get
from display_statistics import display_statistics_working


MOSCOW_ID_HH = 1
MOSCOW_ID_SJ = 4


def predict_rub_salarys_for_HeadHunter(vacancies: list) -> list[int]:
    """Модуль предназначен, чтобы найти приблизительную заработной плату, указанную в вакансии с HeadHunter.

    Args:
        list_vacancies_by_page (list): Получает список вакансий n-го количества страниц 

    Returns:
        list[int]: Возвращает список, с приблизительной зарабатной платой
    """
    vacancy_salaries = []

    for vacancy in vacancies:
        
        salary = vacancy['salary']
        
        if not salary:
            continue
        if salary['currency'] != 'RUR':
            continue
        
        payment_from = salary['from'] if salary['from'] else 0
        payment_to = salary['to'] if salary['to'] else 0

        if not payment_from and not payment_to:
            continue
        average_salary = predict_salary(payment_from, payment_to)
        vacancy_salaries.append(int(average_salary))

    return vacancy_salaries


def predict_rub_salarys_for_SuperJob(vacancies: list) -> list[int]:
    """Модуль предназначен, чтобы найти приблизительную заработной плату, указанную в вакансии с SuperJob.

    Args:
        list_vacancies (list): Получает список вакансий

    Returns:
        list[int]: Возвращает список, с приблизительной зарабатной платой
    """
    vacancy_salaries = []
    
    for vacancy in vacancies:
        payment_from = vacancy['payment_from']
        payment_to = vacancy['payment_to']
        currency = vacancy['currency']
        
        if (not payment_from and not payment_to) or currency != 'rub':
            continue
        average_salary = predict_salary(payment_from, payment_to)
        vacancy_salaries.append(int(average_salary))
    
    return vacancy_salaries


def predict_salary(salary_from: int, salary_to: int) -> int:
    """Вычисляет приблизительную заработную плату.

    Args:
        salary_from (int): Заработная плата, от
        salary_to (int): Заработная плата, до

    Returns:
        int: Приблизительная заработная плата
    """
    if not salary_to:
        return(salary_from * 1.2)
    if not salary_from:
        return(salary_to * 0.8)
    return((salary_from + salary_to) / 2)


def collect_job_statistics_from_HeadHunter(programming_languages: list[str]) -> dict:
    """Сбор статистики запрашиваемых вакансий с сайта HeadHunter.

    Args:
        vacancies (list[str]): Запрашиваемые вакансии

    Returns:
        dict: Статистика запрашиваемых вакансий
    """
    vacancy_statistics = {}

    for programming_language in programming_languages:
        found_vacancies = []

        total_vacancies = None
        page = 0
        pages_number = 1

        while page < pages_number:
            payload = payload = {'text': programming_language, 'area': MOSCOW_ID_HH, 'enable_snippets': 'true', 'page': page, 'per_page': 100}

            page_response = get('https://api.hh.ru/vacancies', params=payload)
            page_response.raise_for_status()

            page_payload = page_response.json()
            found_vacancies.extend(page_payload['items'])

            if pages_number != page_payload['pages']:
                pages_number = page_payload['pages']
            if not total_vacancies:
                total_vacancies = page_payload['found']
            
            page += 1

        vacancy_salaries = predict_rub_salarys_for_HeadHunter(found_vacancies)

        vacancy_statistics[programming_language] = {"vacancies_found": total_vacancies,
                                        "vacancies_processed": len(vacancy_salaries), 
                                        "average_salary": int(sum(vacancy_salaries)/len(vacancy_salaries)) if len(vacancy_salaries) 
                                                                                                       else None}
    return vacancy_statistics


def collect_job_statistics_from_SuperJob(programming_languages: list[str], key: str) -> dict:
    """Сбор статистики запрашиваемых вакансий с сайта SuperJob.

    Args:
        vacancies (list[str]): Запрашиваемые вакансии

    Returns:
        dict: Статистика запрашиваемых вакансий
        key: Ключ доступа к API
    """
    headers = {'X-Api-App-Id': key}

    vacancy_statistics = {}

    for programming_language in programming_languages:
        found_vacancies = []
        total_vacancies = None
        page = 0
        continuation_pages = True

        while continuation_pages:
            payload = {'town': MOSCOW_ID_SJ, 'keyword': programming_language, 'page': page}

            response = get('https://api.superjob.ru/2.0/vacancies/', headers=headers, params=payload)
            response.raise_for_status()

            page_payload = response.json()
            continuation_pages = page_payload['more']
            found_vacancies.extend(page_payload['objects'])
            page += 1

            if not total_vacancies:
                total_vacancies = page_payload['total']

        vacancy_salaries = predict_rub_salarys_for_SuperJob(found_vacancies)
        
        vacancy_statistics[programming_language] = {"vacancies_found": total_vacancies,
                                        "vacancies_processed": len(vacancy_salaries), 
                                        "average_salary": int(sum(vacancy_salaries)/len(vacancy_salaries)) if len(vacancy_salaries) 
                                                                                                       else None}
    
    return vacancy_statistics


def main():
    """Позволяет работать из командной строки
    """
    load_dotenv()
    secret_key = os.getenv('SECRET_KEY_SUPER_JOB')

    parser = argparse.ArgumentParser(description= 'Shows job statistics from Headhunter and SuperJob')
    parser.add_argument('Vacancies', type=str, nargs='+', default='Программист', help='Enter a list of professions that you are interested in')
    args = parser.parse_args()

    vacancies = args.Vacancies
    display_statistics_working(collect_job_statistics_from_HeadHunter(vacancies), 'HeadHunter MOSCOW')
    display_statistics_working(collect_job_statistics_from_SuperJob(vacancies, key=secret_key), 'SuperJob MOSCOW')


if __name__ == '__main__':
    main()