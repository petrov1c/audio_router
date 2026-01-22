"""
Schema-Guided Reasoning (SGR) Demo with OpenAI

This Python code demonstrates Schema-Guided Reasoning (SGR) with OpenAI. It:
- Implements a business agent capable of planning and reasoning
- Implements tool calling using only SGR and simple dispatch
- Uses a simple (inexpensive) non-reasoning model for that

To give this agent something to work with, we ask it to help with running
a small business - selling courses to help achieve AGI faster.

Once this script starts, it will emulate in-memory CRM with invoices,
emails, products and rules. Then it will execute sequentially a set of
tasks (see TASKS below). In order to carry them out, Agent will have to use
tools to issue invoices, create rules, send emails, and a few others.

Read more about SGR by Rinat Abdullin: http://abdullin.com/schema-guided-reasoning/
This demo is described in more detail here: https://abdullin.com/schema-guided-reasoning/demo
"""

from typing import List, Union, Literal, Annotated
from annotated_types import MaxLen, Le, MinLen
from pydantic import BaseModel, Field
import json
import time
import os
import dotenv
from datetime import datetime
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.tree import Tree

dotenv.load_dotenv()

DB = {
    "rules": [],
    "invoices": {},
    "emails": [],
    "products": {
        "SKU-205": {"name": "AGI 101 Course Personal", "price": 258},
        "SKU-210": {"name": "AGI 101 Course Team (5 seats)", "price": 1290},
        "SKU-220": {"name": "Building AGI - online exercises", "price": 315},
    },
}


class SendEmail(BaseModel):
    tool: Literal["send_email"]
    subject: str
    message: str
    files: List[str]
    recipient_email: str


class GetCustomerData(BaseModel):
    tool: Literal["get_customer_data"]
    email: str


class CreateInvoice(BaseModel):
    tool: Literal["create_invoice"]
    email: str
    skus: List[str]
    discount_percent: Annotated[int, Le(50)]


class VoidInvoice(BaseModel):
    tool: Literal["void_invoice"]
    invoice_id: str
    reason: str


class CreateRule(BaseModel):
    tool: Literal["create_rule"]
    email: str
    rule: str


class ReportTaskCompletion(BaseModel):
    tool: Literal["report_task_completion"]
    completed_steps_laconic: List[str]
    code: Literal["completed", "failed"]


class NextStep(BaseModel):
    current_state: str
    plan_remaining_steps_brief: Annotated[List[str], MinLen(1), MaxLen(5)] = Field(..., description="план действий")
    task_completed: bool
    function: Union[
        ReportTaskCompletion,
        SendEmail,
        GetCustomerData,
        CreateInvoice,
        VoidInvoice,
        CreateRule,
    ] = Field(..., description="выполни первый шаг")


# Global report logger
class MarkdownReporter:
    def __init__(self):
        self.reset()

    def reset(self):
        self.content = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.content.append(f"# Agent Execution Report\n")
        self.content.append(f"**Generated:** {timestamp}\n\n")
        self.content.append("## Available Products\n")
        for sku, product in DB["products"].items():
            self.content.append(f"- **{sku}**: {product['name']} - ${product['price']:,.2f}")
        self.content.append("\n---\n\n")

    def add_task_header(self, task_idx, task):
        self.content.append(f"## Task {task_idx}: {task}\n")

    def add_step(self, step_num, action, function_data, result):
        self.content.append(f"### Step {step_num}\n")
        self.content.append(f"**Action:** {action}\n\n")
        self.content.append(f"**Function:** `{function_data.get('tool', 'unknown')}`\n\n")

        if isinstance(result, dict):
            self.content.append("**Result:**\n```json\n")
            self.content.append(json.dumps(result, indent=2))
            self.content.append("\n```\n\n")
        else:
            self.content.append(f"**Result:** {result}\n\n")

    def add_task_completion(self, status, steps):
        icon = "✅" if status == "completed" else "❌"
        self.content.append(f"### Task Result: {icon} {status.upper()}\n")
        self.content.append("**Completed Steps:**\n")
        for step in steps:
            self.content.append(f"- {step}")
        self.content.append("\n---\n\n")

    def save_report(self, filename=None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_report_{timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.content))
        return filename


def format_currency(amount):
    return f"${amount:,.2f}"


def format_tool_result(result, tool_name):
    console = Console()

    if isinstance(result, str):
        return Panel(result, title=f"🔧 {tool_name.replace('_', ' ').title()}",
                     title_align="left", border_style="yellow")

    if tool_name == "send_email":
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_row("📧", f"[cyan]To:[/cyan] {result['to']}")
        table.add_row("📝", f"[cyan]Subject:[/cyan] {result['subject']}")
        table.add_row("💬", f"[cyan]Message:[/cyan] {result['message']}")
        return Panel(table, title="📨 Email Sent", title_align="left", border_style="green")

    elif tool_name == "remember":
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_row("👤", f"[cyan]Customer:[/cyan] {result['email']}")
        table.add_row("📋", f"[cyan]Rule:[/cyan] {result['rule']}")
        return Panel(table, title="🧠 Rule Created", title_align="left", border_style="blue")

    elif tool_name == "issue_invoice":
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_row("🆔", f"[cyan]Invoice ID:[/cyan] {result['id']}")
        table.add_row("👤", f"[cyan]Customer:[/cyan] {result['email']}")
        table.add_row("🛍️", f"[cyan]Products:[/cyan] {', '.join(result['skus'])}")
        table.add_row("💰", f"[cyan]Total:[/cyan] {format_currency(result['total'])}")
        if result['discount_percent'] > 0:
            table.add_row("🎯",
                          f"[cyan]Discount:[/cyan] {result['discount_percent']}% ({format_currency(result['discount_amount'])})")
        table.add_row("📄", f"[cyan]File:[/cyan] {result['file']}")
        return Panel(table, title="🧾 Invoice Generated", title_align="left", border_style="green")

    elif tool_name == "get_customer_data":
        tree = Tree("👤 Customer Data")

        rules_node = tree.add("📋 Rules")
        for rule in result.get('rules', []):
            rules_node.add(f"• {rule['rule']}")

        invoices_node = tree.add("🧾 Invoices")
        for inv_id, invoice in result.get('invoices', []):
            status = "❌ VOID" if invoice.get('void') else "✅ Active"
            invoices_node.add(f"• {inv_id}: {format_currency(invoice['total'])} {status}")

        emails_node = tree.add("📧 Emails")
        for email in result.get('emails', []):
            emails_node.add(f"• {email['subject']}")

        return Panel(tree, title="📊 Customer Profile", title_align="left", border_style="cyan")

    return Panel(str(result), title=f"🔧 {tool_name.replace('_', ' ').title()}",
                 title_align="left", border_style="white")


def dispatch(cmd: BaseModel):
    if isinstance(cmd, SendEmail):
        email = {
            "to": cmd.recipient_email,
            "subject": cmd.subject,
            "message": cmd.message,
        }
        DB["emails"].append(email)
        return email

    if isinstance(cmd, CreateRule):
        rule = {
            "email": cmd.email,
            "rule": cmd.rule,
        }
        DB["rules"].append(rule)
        return rule

    if isinstance(cmd, GetCustomerData):
        addr = cmd.email
        return {
            "rules": [r for r in DB["rules"] if r["email"] == addr],
            "invoices": [t for t in DB["invoices"].items() if t[1]["email"] == addr],
            "emails": [e for e in DB["emails"] if e.get("to") == addr],
        }

    if isinstance(cmd, CreateInvoice):
        total = 0.0
        for sku in cmd.skus:
            product = DB["products"].get(sku)
            if not product:
                return f"Product {sku} not found"
            total += product["price"]

        discount = round(total * 1.0 * cmd.discount_percent / 100.0, 2)
        invoice_id = f"INV-{len(DB['invoices']) + 1}"

        invoice = {
            "id": invoice_id,
            "email": cmd.email,
            "file": f"/invoices/{invoice_id}.pdf",
            "skus": cmd.skus,
            "discount_amount": discount,
            "discount_percent": cmd.discount_percent,
            "total": total - discount,
            "void": False,
        }
        DB["invoices"][invoice_id] = invoice
        return invoice

    if isinstance(cmd, VoidInvoice):
        invoice = DB["invoices"].get(cmd.invoice_id)
        if not invoice:
            return f"Invoice {cmd.invoice_id} not found"
        invoice["void"] = True
        return invoice


TASKS = [
    "Создай правило: клиенту sama@openai.com всегда давай скидку 5%.",
    "Создай правило для elon@x.com: Отправляй его счета на finance@x.com.",
    "sama@openai.com хочет приобрести по одной штуке каждого товара из списка товаров. Отправь ему счет по электронной почте.",
    "elon@x.com хочет в 2 раза больше, чем заказал sama@openai.com. Отправь счет.",
    "повтори последний счет elon@x.com: примени 3-кратную скидку от sama@openai.com.",
]

system_prompt = f"""
Ты являешься помошником по взаимодействию с клиентами. Тебе доступны следующие активности:

<Actions>
    get_customerd_data # получает данные клиента из базы данных
    create_rule # записывает правило взаимодействия с клиентом в базу данных
    send_email # отправляет электронное письмо
    create_invoice # создает счет
    void_invoice # удаляет счет
    report_task_completion # пишет отчет о выполнении задачи
</Actions> 

<Main_rules>
    Напиши, что тебя просят сделать. 
    Составь план действий.
    Напиши отчет о выполненной задаче
</Main_rules>

<Rules>
    Всегда проверяй данные клиента перед выставлением счетов.
    Всегда отправляй клиентам электронные письма после выставления счетов.
</Rules>

Products: {DB["products"]}""".strip()

# client = OpenAI(base_url="https://routerai.ru/api/v1", api_key=os.getenv("API_KEY"))
client = OpenAI(base_url="http://0.0.0.0:8000/v1", api_key='-')
console = Console()
print = console.print
reporter = MarkdownReporter()


def print_header():
    header_text = Text("🤖 Schema-Guided Reasoning Agent", style="bold magenta")
    subtitle_text = Text("Business Automation & Customer Management", style="italic cyan")

    print(Panel(
        Align.center(header_text + "\n" + subtitle_text),
        border_style="magenta",
        padding=(1, 2)
    ))


def print_products_table():
    table = Table(title="📦 Available Products", show_header=True, header_style="bold cyan")
    table.add_column("SKU", style="yellow", no_wrap=True)
    table.add_column("Product Name", style="green")
    table.add_column("Price", style="magenta", justify="right")

    for sku, product in DB["products"].items():
        table.add_row(sku, product["name"], format_currency(product["price"]))

    print(table)
    print()


def execute_tasks():
    print_header()
    print_products_table()

    for task_idx, task in enumerate(TASKS, 1):
        task_header = Text(f"Task {task_idx}", style="bold white on blue")
        task_content = Text(task, style="bold white")

        print(Panel(
            task_header + "\n" + task_content,
            title="🎯 New Mission",
            title_align="left",
            border_style="blue",
            padding=(1, 2)
        ))

        # Log task to markdown
        reporter.add_task_header(task_idx, task)

        log = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task}
        ]

        steps_completed = []

        for i in range(5):
            step = f"step_{i + 1}"

            step_text = Text(f"🧠 Planning {step}...", style="bold yellow")
            print(step_text)

            time.sleep(0.5)

            try:
                completion = client.beta.chat.completions.parse(
                    model="Qwen/Qwen3-VL-8B-Instruct", # 'qwen/qwen3-vl-32b-instruct'
                    response_format=NextStep,
                    messages=log,
                    temperature=0,
                    top_p=1,
                    extra_body= {
                        'chat_template_kwargs': {"enable_thinking": False},
                    },
                    # max_completion_tokens=10000,
                )
                job = completion.choices[0].message.parsed
            except Exception as e:
                print(Panel(f"Error: {str(e)}", title="API Error", border_style="red"))
                break

            if isinstance(job.function, ReportTaskCompletion):
                status_color = "green" if job.function.code == "completed" else "red"
                status_icon = "✅" if job.function.code == "completed" else "❌"

                print(Panel(
                    f"{status_icon} Task {job.function.code.upper()}",
                    style=f"bold {status_color}",
                    border_style=status_color
                ))

                steps_table = Table(title="📋 Completed Steps", show_header=False)
                steps_table.add_column("Step", style="cyan")

                for step_desc in job.function.completed_steps_laconic:
                    steps_table.add_row(f"✓ {step_desc}")

                print(steps_table)
                print(Rule(style="dim"))

                # Log completion to markdown
                reporter.add_task_completion(job.function.code, job.function.completed_steps_laconic)
                break

            next_step = job.plan_remaining_steps_brief[0]
            print(Panel(
                f"🎯 [bold cyan]Next Action:[/bold cyan] {next_step}",
                border_style="cyan"
            ))

            log.append({
                "role": "assistant",
                "content": next_step,
                "tool_calls": [{
                    "type": "function",
                    "id": step,
                    "function": {
                        "name": job.function.tool,
                        "arguments": job.function.model_dump_json(),
                    }}]
            })

            result = dispatch(job.function)

            # Log step to markdown
            reporter.add_step(i + 1, next_step, {"tool": job.function.tool}, result)

            formatted_result = format_tool_result(result, job.function.tool)
            print(formatted_result)

            txt = result if isinstance(result, str) else json.dumps(result)
            log.append({"role": "tool", "content": txt, "tool_call_id": step})

            steps_completed.append(next_step)

            print()

        print("\n" + "=" * 80 + "\n")

    # Save the markdown report
    filename = reporter.save_report()
    print(Panel(
        f"📄 Report saved to: {filename}",
        title="Report Generated",
        border_style="green"
    ))


if __name__ == "__main__":
    execute_tasks()