from create_database import initialize_database
from services.user_service import count_users
from gui.initial_admin_window import run_initial_admin_setup
from gui.main_window import MainWindow


if __name__ == "__main__":
    initialize_database()

    if count_users() == 0:
        setup_completed = run_initial_admin_setup()

        if not setup_completed:
            raise SystemExit

    app = MainWindow()
    app.run()
