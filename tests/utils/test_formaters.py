import random
from unittest.mock import Mock

import pytest

from src.services.advices import Advice
from src.services.leaders import Leader, UserInLeaders
from src.services.questions import Question
from src.utils.formaters import format_advice, format_explanation, format_leaders_message, format_question


@pytest.fixture
def test_question() -> Question:
    """A fixture for creating a test question object"""
    return Question(
        id=1,
        text='text',
        choices={'A': 1, 'B': 2},
        answer='A',
        explanation='explanation'
    )


def test_format_question(test_question: Question) -> None:
    # act
    res = format_question(question=test_question)

    # assert
    assert res == (
        'text\n\n'
        '*A\\)* 1\n'
        '*B\\)* 2'
    )


def test_format_explanation__correct_answer(test_question: Question) -> None:
    # arrange
    random.choice = Mock(return_value=r'Правильный ответ\! 👍')
    user_answer = 'A'
    is_correct = True

    # act
    result = format_explanation(test_question, is_correct, user_answer)

    # assert
    assert result == (
        "\ntext\n\n"
        "*Правильный ответ:* A\\) 1\n"
        "*Твой выбор:* A\\) 1\n\n"
        "Правильный ответ\\! 👍\n\n"
        "*Объяснение:*\n"
        "explanation"
    )


def test_format_explanation__incorrect_answer(test_question: Question) -> None:
    # arrange
    random.choice = Mock(return_value=r"Упс, мимо\! 🙊")
    user_answer = "B"
    is_correct = False

    # act
    result = format_explanation(test_question, is_correct, user_answer)

    # assert
    assert result == (
        "\ntext\n\n"
        "*Правильный ответ:* A\\) 1\n"
        "*Твой выбор:* B\\) 2\n\n"
        "Упс, мимо\\! 🙊\n\n"
        "*Объяснение:*\nexplanation"
    )


def test_format_advice() -> None:
    # act
    res = format_advice(
        advice=Advice(
            advice_id=1,
            theme='lists',
            level=1,
            link='https://python.com/useful_link_to_handle_with_lists'
        )
    )

    # assert
    assert res == (
        'Я понял, что тебе стоит подтянуть тему *lists*\\.\n'
        'Вот [ссылка](https://python.com/useful_link_to_handle_with_lists)\n'
        'Прочти, чтобы стать еще круче\\!'
    )


def test_format_leaders_message() -> None:
    # arrange
    leaders = [
        Leader(id=1, first_name='User1', username='user1', score=12),
        Leader(id=2, first_name='User2', username='user2', score=3),
        Leader(id=3, first_name='User3', username='user3', score=1),
    ]
    user_in_leaders = UserInLeaders(score=12, position=1)

    # act
    formatted_message = format_leaders_message(leaders=leaders, user_in_leaders=user_in_leaders)

    # assert
    assert formatted_message == (
        '*Таблица лидеров:*\n'
        '1\\. [User1](https://t.me/user1) \\- 12 баллов\n'
        '2\\. [User2](https://t.me/user2) \\- 3 балла\n'
        '3\\. [User3](https://t.me/user3) \\- 1 балл\n'
        '\n'
        '*Твое текущее место:* 1\n'
        '*Ты набрал* 12 баллов'
    )


def test_format_leaders_message__user_not_found() -> None:
    leaders = [
        Leader(id=1, first_name='User1', username='user1', score=10),
        Leader(id=2, first_name='User2', username='user2', score=20),
        Leader(id=3, first_name='User3', username='user3', score=15),
    ]

    formatted_message = format_leaders_message(leaders=leaders, user_in_leaders=None)

    expected_message = (
        '*Таблица лидеров:*\n'
        '1\\. [User1](https://t.me/user1) \\- 10 баллов\n'
        '2\\. [User2](https://t.me/user2) \\- 20 баллов\n'
        '3\\. [User3](https://t.me/user3) \\- 15 баллов\n'
    )
    assert formatted_message == expected_message
