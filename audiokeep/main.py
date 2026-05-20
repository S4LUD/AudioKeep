"""Application entry point."""


def main() -> None:
    from audiokeep.app import App
    from audiokeep.config.store import SettingsStore
    from audiokeep.system.autostart import set_auto_start
    from audiokeep.system.logging_setup import setup_logging
    from audiokeep.system.paths import config_file, log_dir
    from audiokeep.system.single_instance import SingleInstance

    lock = SingleInstance()
    if not lock.acquire():
        return

    setup_logging(log_dir())

    store = SettingsStore(config_file())
    set_auto_start(store.settings.auto_start)

    app = App(store)

    if not store.settings.start_minimized:
        app.open_settings()

    try:
        app.run()
    except KeyboardInterrupt:
        app.shutdown()
    finally:
        lock.release()


if __name__ == "__main__":
    main()
