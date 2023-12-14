# Yatube
### Описание проекта:

Проект **Yatube** - это социальная сеть, где пользователи могут публиковать 
посты на любые темы (с фотографиями и без), а так же подписываться на других 
пользователей, чтобы не пропустить интересные новости.

### Стек технологий:

- Python 3.9.10
- Django 2.2.16
- SQLite
- pytest

### Запуск проекта:

<br>1. Клонировать репозиторий:

```
git clone "адрес клонируемого репозитория"
```

<br>2. В корневой директории создать и активировать виртуальное окружение:

```
python -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

<br>3. Установить и обновить пакетный менеджер:

```
python -m pip install --upgrade pip
```

<br>4. Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

<br>5. Перейти в папку **yatube** и выполнить миграции:

```
cd yatube
```

```
python manage.py makemigrations
```

```
python manage.py migrate
```

<br>6. Запустить проект:

```
python manage.py runserver
```

### Project's preview:

* **Главная страница**
  
    ![Главная страница!](preview/main_page.png)

* **Страница регистрации**
 
    ![Страница регистрации!](preview/sign_up.png)

* **Страница создания поста**
  
    ![Страница создания поста!](preview/create_post.png)

* **Страница поста**

    ![Страница поста!](preview/post.png)

* **Подписки**

    ![Подписки!](preview/follow.png)

### Автор проекта:

Семёнова Юлия (GitHub: JuliSem)