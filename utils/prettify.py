from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED

__all__ = (
    "print_channels_info", 
    "print_settings", 
    "print_processing_time", 
    "print_token_stats",
)

console = Console()


def print_channels_info(guild: str, channels: list[dict]) -> None:
    """Улучшает вывод информации"""
    
    # Таблица каналов сервера
    table = Table(title="Каналы сервера", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Название", style="green")
    
    for channel in channels:
        table.add_row(str(channel.get("id", "")), channel.get("name", ""))
    
    # Информацию о сервере
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]Сервер:[/] [yellow]{guild}[/]",
        title="Информация о сервере",
        border_style="blue",
        padding=(1, 4)
    ))
    
    # Отображает табличку
    console.print(table)
    console.print()


def _get_noun(number: int, one: str, two: str, five: str) -> str:
    number %= 100
    if number >= 5 and number <= 20:
        return five
    number %= 10
    if number == 1:
        return one
    if number >= 2 and number <= 4:
        return two
    return five


def print_settings(settings: dict) -> None:
    """Улучшает отображение настроек"""
    
    # Создание панельки
    settings_text = Text()
    settings_text.append("Настройки бота\n", style="bold cyan")
    
    # Создание таблицы
    table = Table(
        box=ROUNDED,
        show_header=False,
        show_edge=True,
        width=60,
        padding=(0, 2)
    )
    table.add_column("Ключ", style="dim", width=20)
    table.add_column("Значение", style="green", width=38, overflow="fold")
    
    # Добавление строк, учитывая секретные данные
    for key, value in settings.items():
        if key == "discord_tokens":
            token_noun = _get_noun(len(value), "токен", "токена", "токенов")
            display_value = f"[red][{len(value)} {token_noun}][/]"
        elif key == "image_path" and not value:
            display_value = "[dim]Не указано[/]"
        else:
            display_value = str(value)
        
        table.add_row(
            Text(key, style="bold"),
            Text.from_markup(display_value)
        )
    
    # Билд панели
    console.print()
    console.print(Panel.fit(
        table,
        title="[reverse] ТЕКУЩИЕ НАСТРОЙКИ [/]",
        border_style="bright_blue",
        padding=(1, 4)
    ))
    
    # Добавление предупреждение о показе токенов
    console.print(
        Panel.fit(
            "[yellow]⚠️ Токены скрыты для безопасности. Храните их в секрете![/]",
            border_style="yellow",
            width=60
        )
    )
    console.print()


def print_processing_time(processing_time) -> None:
    console.print(f"[bold dim]├────────────────────────────────────────┤[/]")
    console.print(f"[bold dim]│ [bold not dim]СТАТУС:[/] [green]ВЫПОЛНЕНО[/] [bold not dim]| ВРЕМЯ:[/] [bright_cyan]{processing_time:.4f}s[/] [bold dim]│[/]")
    console.print(f"[bold dim]└────────────────────────────────────────┘[/]")


def print_token_stats(token: str, sended_messages: int, failed_messages: int) -> None:
    """Красивый вывод статистики рассылки"""
    total_messages = sended_messages + failed_messages
    
    # Создаем таблицу для статистики
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column(justify="left")
    stats_table.add_column(justify="left")
    
    stats_table.add_row(
        "🔹 Токен:",
        Text(f"{token[:20]}...", style="bold yellow")
    )
    stats_table.add_row(
        "📊 Всего:",
        Text(str(total_messages), style="bold deep_sky_blue1")
    )
    stats_table.add_row(
        "✅ Успешные:",
        Text(str(sended_messages), style="bold green")
    )
    stats_table.add_row(
        "❌ Неуспешные:",
        Text(str(failed_messages), style="bold red")
    )
    
    # Выводим в панели
    console.print()
    console.print(Panel.fit(
        stats_table,
        title="[bold]Статистика рассылки[/]",
        border_style="blue",
        padding=(1, 4)
    ))
    console.print()