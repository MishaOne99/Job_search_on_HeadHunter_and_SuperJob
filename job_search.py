'''Выводит в таблице, статистику запрашиваемых вакансий с HeadHunter и SuperJob'''


import os
import argparse
from dotenv import load_dotenv
from requests import get
from display_statistics import display_statistics_working


ID_MOSCOW_HH = 1
ID_MOSCOW_SJ = 4


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
        
        if salary is None:
            continue
        if salary['currency'] != 'RUR':
            continue
        payment_from = salary['from'] if salary['from'] else 0
        payment_to = salary['to'] if salary['to'] else 0
        
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
        
        if (payment_from == 0 and payment_to == 0) or currency != 'rub':
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


def collect_job_statistics_from_HeadHunter(vacanсies: list[str]) -> dict:
    """Сбор статистики запрашиваемых вакансий с сайта HeadHunter.

    Args:
        vacancies (list[str]): Запрашиваемые вакансии

    Returns:
        dict: Статистика запрашиваемых вакансий
    """
    statistic_vacancies = {}

    for vacancy in vacanсies:
        found_vacancies = []

        total_vacancies = None
        page = 0
        pages_number = 1

        while page < pages_number:
            payload = payload = {'text': vacancy, 'area': ID_MOSCOW_HH, 'enable_snippets': 'true', 'page': page, 'per_page': 100}

            page_response = get('https://api.hh.ru/vacancies', params=payload)
            page_response.raise_for_status()

            page_payload = page_response.json()
            found_vacancies.extend(page_payload['items'])

            if pages_number != page_payload['pages']:
                pages_number = page_payload['pages']
            if not total_vacancies:
                total_vacancies = page_payload['found']
            
            page += 1

        salary_vacancy = predict_rub_salarys_for_HeadHunter(found_vacancies)

        statistic_vacancies[vacancy] = {"vacancies_found": total_vacancies,
                                        "vacancies_processed": len(salary_vacancy), 
                                        "average_salary": int(sum(salary_vacancy)/len(salary_vacancy)) if len(salary_vacancy) != 0 
                                                                                                       else None}
    return statistic_vacancies


def collect_job_statistics_from_SuperJob(vacanсies: list[str]) -> dict:
    """Сбор статистики запрашиваемых вакансий с сайта SuperJob.

    Args:
        vacancies (list[str]): Запрашиваемые вакансии

    Returns:
        dict: Статистика запрашиваемых вакансий
    """
    secret_key = os.getenv('SECRET_KEY_SUPER_JOB')
    headers = {'X-Api-App-Id': secret_key}

    statistic_vacancies = {}

    for vacancy in vacanсies:
        found_vacancies = []
        total_vacancies = None
        page = 0
        continuation_pages = True

        while continuation_pages:
            payload = {'town': ID_MOSCOW_SJ, 'keyword': vacancy, 'page': page}

            response = get('https://api.superjob.ru/2.0/vacancies/', headers=headers, params=payload)
            response.raise_for_status()

            page_payload = response.json()
            continuation_pages = page_payload['more']
            found_vacancies.extend(page_payload['objects'])
            page += 1

            if not total_vacancies:
                total_vacancies = page_payload['total']

        salary_vacancy = predict_rub_salarys_for_SuperJob(found_vacancies)
        
        statistic_vacancies[vacancy] = {"vacancies_found": total_vacancies,
                                        "vacancies_processed": len(salary_vacancy), 
                                        "average_salary": int(sum(salary_vacancy)/len(salary_vacancy)) if len(salary_vacancy) != 0 
                                                                                                       else None}
    
    return statistic_vacancies


def main():
    """Позволяет работать из командной строки
    """
    parser = argparse.ArgumentParser(description= 'Shows job statistics from Headhunter and SuperJob')
    parser.add_argument('Vacancies', type=str, nargs='+', default='Программист', help='Enter a list of professions that you are interested in')
    args = parser.parse_args()

    vacancies = args.Vacancies
    display_statistics_working(collect_job_statistics_from_HeadHunter(vacancies), 'HeadHunter MOSCOW')
    display_statistics_working(collect_job_statistics_from_SuperJob(vacancies), 'SuperJob MOSCOW')


if __name__ == '__main__':
    load_dotenv()
    main()