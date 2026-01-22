"""
This Python code demonstrates Schema-Guided Reasoning (SGR) with llama.cpp and small model - Qwen3-4B Q8_0. It:

- implements a business agent capable of planning and reasoning
- implements tool calling using only SGR and simple dispatch
- uses with a simple (inexpensive) non-reasoning model for that

This demo is modified from https://abdullin.com/schema-guided-reasoning/demo to support local llm

Test model: Qwen3-4B-Instruct-2507-Q8_0 (https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q8_0.gguf)
Command to start llama.cpp server: ./llama-server -m /content/Qwen3-4B-Instruct-2507-Q8_0.gguf -ngl 999 --port 12345 --threads -1 --host 127.0.0.1 --ctx-size 20000
"""

### local llm:
import uuid
import json
import requests
from urllib import request, parse
from urllib.request import urlopen
import urllib.parse
import ssl
import re
import time

### -----------------------------------------------------------------------
### local llm provider:
### -----------------------------------------------------------------------
class LocalLLM:
    ### init:
    def __init__(
        self,
        url="http://localhost:12345/completion",
        api_key=None,
        llm_type="qwen",
    ):
        self.url = url
        self.retries = 3
        self.api_key = api_key
        self.llm_type = llm_type
        ### Qwen:
        self.prompt_template = (
            "<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        )
        self.system_message = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant and should always reply in Russian language"
    
    ### execute:
    def get_completion_messages(
        self,
        messages,
        json_grammar=None,
        n_predict=128,
        temperature=0.3
    ):
        attempts = 0
        ### retry:
        while attempts < self.retries:
            result = self._get_completion_messages(
                messages, json_grammar, n_predict, temperature
            )
            if result is not None:
                return result
            else:
                attempts += 1
        return None

    ### execute:
    def _get_completion_messages(
        self,
        messages,
        json_grammar=None,
        n_predict=128,
        temperature=0.5
    ):
        headers = {"Content-Type": "application/json"}

        if self.api_key is not None and len(self.api_key) > 0:
            headers["Authorization"] = "Bearer " + self.api_key

        ### create prompt:
        prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                prompt += f"<|im_start|>system\n{msg["content"]}<|im_end|>\n"
            elif msg["role"] == "user":
                prompt += f"<|im_start|>user\n{msg["content"]}<|im_end|>\n"
            elif msg["role"] == "assistant":
                if "tool_call" in msg:
                    prompt += "<|im_start|>assistant\n" + "<tool_call>\n{" + '"name": "' + msg["tool_call"]["name"] + '", "arguments" : "' + json.dumps(msg["tool_call"]["arguments"]) + '"}' + "\n</tool_call><|im_end|>\n"
                else:
                    prompt += f"<|im_start|>assistant\n{msg["content"]}<|im_end|>\n"
            elif msg["role"] == "tool":
                ad = f"<|im_start|>user\n<tool_response>\n{msg["content"]}\n</tool_response><|im_end|>\n"
                prompt += ad
                #print(ad)
        prompt += "<|im_start|>assistant\n"

        payload = {
            "stream": False,
            "cache_prompt" : True,
            "n_predict": n_predict,
            "temperature": temperature,
            ### qwen3:
            "top_k" : 20,
            "top_p" : 0.8,
            "min_p" : 0.01,
            ### gemma:
            "repeat_penalty": 1.1,
            #"top_k": 64,
            #"top_p": 0.95,
            "stop" : ['<|im_end|', '</s>', "<end_of_turn>"],
            #+ "/no_think"
            "prompt": prompt,
        }

        if json_grammar is not None:
            payload["json_schema"] = json_grammar

        try:
            response = requests.post(self.url, headers=headers, json=payload)
            # Raises HTTPError for bad responses (4xx or 5xx)
            response.raise_for_status()
            json_resp = response.json()
            content = json_resp["content"]
            ### if qwen:
            if self.llm_type == "qwen":
                pattern = r'<think>.*?</think>'
                # Remove all occurrences of the pattern (using re.DOTALL to match across newlines)
                cleaned_text = re.sub(pattern, '', content, flags=re.DOTALL)
                content = cleaned_text.strip()

            ### strip possible json```
            text = content.strip()
            ### find ```json
            idx = text.find("```json", 0)
            if idx >= 0:
                text = text[idx + 7:]
                idx1 = text.find("```", 0)
                if idx1 >= 0:
                    text = text[:idx1]
            else:
                idx = text.find("```", 0)
                if idx >= 0:
                    text = text[idx + 3:]
                    idx1 = text.find("```", 0)
                    if idx1 >= 0:
                        text = text[:idx1]
            content = content.strip('\n').strip('`').strip(' ')
            return content
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while making the request: {e}")
            return None
### -----------------------------------------------------------------------

# create instance:
llm = LocalLLM(url = "http://127.0.0.1:12345/completion", api_key = "", llm_type = "qwen")

# Let's start by implementing our customer management system. For the sake of
# simplicity it will live in memory and have a very simple DB structure
DB = {
    "rules": [],
    "invoices": {},
    "emails": [],
    "products": {
        "SKU-205": { "name":"AGI 101 Course Personal", "price":258},
        "SKU-210": { "name": "AGI 101 Course Team (5 seats)", "price":1290},
        "SKU-220": { "name": "Building AGI - online exercises", "price":315},
    },
}

# Now, let's define a few tools which could be used by LLM to do something 
# useful with this customer management system. We need tools to issue invoices, 
# send emails, create rules and memorize new rules. Maybe a tool to cancel invoices.
from typing import List, Union, Literal, Annotated
from annotated_types import MaxLen, Le, MinLen
from pydantic import BaseModel, Field, TypeAdapter


# Tool: Sends an email with subject, message, attachments to a recipient
class SendEmail(BaseModel):
    tool: Literal["send_email"]
    subject: str
    message: str
    files: List[str]
    recipient_email: str

# Tool: Retrieves customer data such as rules, invoices, and emails from the database
class GetCustomerData(BaseModel):
    tool: Literal["get_customer_data"]
    email: str

# Tool: Issues an invoice to a customer, allowing up to a 50% discount
class IssueInvoice(BaseModel):
    tool: Literal["issue_invoice"]
    email: str
    skus: List[str]
    discount_percent: Annotated[int, Le(50)] # never more than 50% discount

# Tool: Cancels (voids) an existing invoice and records the reason
class VoidInvoice(BaseModel):
    tool: Literal["void_invoice"]
    invoice_id: str
    reason: str

# Tool: Saves a custom rule for interacting with a specific customer
class CreateRule(BaseModel):
    tool: Literal["create_rule"]
    email: str
    rule_text: str


# This function handles executing commands issued by the agent. It simulates
# operations like sending emails, managing invoices, and updating customer
# rules within the in-memory database.
def dispatch(cmd: BaseModel):
    # here is how we can simulate email sending
    # just append to the DB (for future reading), return composed email
    # and pretend that we sent something
    if isinstance(cmd, SendEmail):
        email = {
            "to": cmd.recipient_email,
            "subject": cmd.subject,
            "message": cmd.message,
        }
        DB["emails"].append(email)
        return email


    # likewize rule creation just stores rule associated with customer
    if isinstance(cmd, CreateRule):
        rule = {
            "email": cmd.email,
            "rule": cmd.rule_text,
        }
        DB["rules"].append(rule)
        return rule

    # customer data reading - doesn't change anything. It queries DB for all
    # records associated with the customer
    if isinstance(cmd, GetCustomerData):
        addr = cmd.email
        return {
            "email" : addr,
            "rules": [r for r in DB["rules"] if r["email"] == addr],
            "invoices": [t for t in DB["invoices"].items() if t[1]["email"] == addr],
            "emails": [e for e in DB["emails"] if e.get("to") == addr],
        }

    # invoice generation is going to be more tricky
    # it will demonstrate discount calculation (we know that LLMs shouldn't be trusted
    # with math. It also shows how to report problems back to LLM.
    # ultimately, it computes a new invoice number and stores it in the DB
    if isinstance(cmd, IssueInvoice):
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
            "file": "/invoices/" + invoice_id + ".pdf",
            "skus": cmd.skus,
            "discount_amount": discount,
            "discount_percent": cmd.discount_percent,
            "total": total,
            "void": False,
        }
        DB["invoices"][invoice_id] = invoice
        return invoice


    # invoice cancellation marks a specific invoice as void
    if isinstance(cmd, VoidInvoice):
        invoice = DB["invoices"].get(cmd.invoice_id)
        if not invoice:
            return f"Invoice {cmd.invoice_id} not found"
        invoice["void"] = True
        return invoice


# Now, having such DB and tools, we could come up with a list of tasks
# that we can carry out sequentially
TASKS = [
    # 1. this one should create a new rule for sama
    "Rule: always address sama@openai.com as 'The SAMA', always give him 5% discount.",
    # 2. this should create a rule for elon
    "Rule for elon@x.com: always invoice and email him finance@x.com, do not use elon@x.com",
    # 3. now, this task should create an invoice for sama that includes one of each
    # product. But it should also remember to give discount and address him
    # properly
    "sama@openai.com wants one of each product. Email him the invoice",
    # 4. Even more tricky - we need to create the invoice for Musk based on the
    # invoice of sama, but twice. Plus LLM needs to remeber to use the proper
    # email address for invoices - finance@x.com
    "elon@x.com wants 2x of what sama@openai.com got. Prepare invoice",
    # 5. even more tricky. Need to cancel old invoice (we never told LLMs how)
    # and issue the new invoice. BUT it should pull the discount from sama and
    # triple it. Obviously the model should also remember to send invoice
    # not to elon@x.com but to finance@x.com
    "Void last elon@x.com invoice and make new one: provide the discount - 3x of what sama@openai.com got for the same products and email it to elon",
]

# let's define one more special command. LLM can use it whenever
# it thinks that its task is completed. It will report results with that.
class ReportTaskCompletion(BaseModel):
    tool: Literal["report_completion"]
    completed_steps_laconic: List[str]
    code: Literal["completed", "failed"]

# now we have all sub-schemas in place, let's define SGR schema for the agent
class NextStep(BaseModel):
    # reasoning:
    reasoning_how_to_do_task : str  = Field(..., description="explain your thoughts on how to accomplish - what steps to execute")
    # we'll give some thinking space here
    current_state: str
    # Cycle to think about what remains to be done. at least 1 at most 5 steps
    # we'll use only the first step, discarding all the rest.
    plan_remaining_steps: Annotated[List[str], MinLen(1), MaxLen(5)]
    # now let's continue the cascade and check with LLM if the task is done
    task_completed: bool
    # Routing to one of the tools to execute the first remaining step
    # if task is completed, model will pick ReportTaskCompletion
    next_step: Union[
        ReportTaskCompletion,
        SendEmail,
        GetCustomerData,
        IssueInvoice,
        VoidInvoice,
        CreateRule,
    ] = Field(..., description="execute first remaining step")

type_adapter = TypeAdapter(NextStep)
#print(type_adapter.json_schema())
schema = type_adapter.json_schema()

import json

# here is the prompt with some core context
# since the list of products is small, we can merge it with prompt
# In a bigger system, could add a tool to load things conditionally
system_prompt = f"""
You are a business assistant helping Rinat Abdullin with customer interactions.

- Clearly report when tasks are done.
- Always check customer data before issuing invoices or making changes
- Always send customers emails after issuing invoices (with invoice attached).
- In email with invoices always start with name of the customer if it's known (i.e. Dear <Customer name>), provide total amount invoices and discount applied (if anything)
- No need to wait for payment confirmation before proceeding.
- Be laconic. Especially in emails
- If you are asked to create the Rule - just create the Rule for future usage, do not issue invoice, send email or do another actions after that!
- Before canceling the invoice make sure you get it's ID from the customer profile
- If you are asked to increase quantify of SKUs in order - add same SKU several times in invoic to accomplish that
- Don't forget to check customer profile before invoicing
- Don't do useless tools call and do not repeat calls if it's already done and you have all the information from prev call
- If you asked to cancel / void invoice than do it first before issuing new one
- Always check customer profile before invoicing and sending to get relevant rules for customer: discounts, name, email to send to

You are always starting the task with initial state.
Please carefully plan necessary steps to acomplish the task and respond with next step you will execute.

Products: {DB["products"]}

Your output should be JSON object with schema {json.dumps(schema)}

""".strip()

# now we just need to implement the method to bring that all together
# we will use rich for pretty printing in console
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

console = Console()
print = console.print

### exec message:
def exec_llm(messages, max_completion_tokens):
    global schema
    llmresp = llm.get_completion_messages(
        messages,
        schema,
        max_completion_tokens,
        0.6
    )
    ### debug response:
    #print(llmresp)
    return llmresp


# Runs each defined task sequentially. The AI agent uses reasoning to determine
# what steps are required to complete each task, executing tools as needed.
def execute_tasks():

    # we'll execute all tasks sequentially. You can add your tasks
    # of prompt user to write their own
    for task in TASKS:
        print("\n\n")
        print(Panel(task, title="Launch agent with task", title_align="left"))

        # log will contain conversation context for the agent within task
        log = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task}
        ]

        # let's limit number of reasoning steps by 20, just to be safe
        for i in range(20):
            step = f"step_{i+1}"
            print(f"Planning {step}... ", end="")

            # This sample relies on OpenAI API. We specifically use 4o, since
            # GPT-5 has bugs with constrained decoding as of August 14, 2025
            completion = exec_llm(log, max_completion_tokens=5000)
            job = NextStep.model_validate_json(completion)

            # if SGR decided to finish, let's complete the task
            # and quit this loop
            if isinstance(job.next_step, ReportTaskCompletion):
                print(f"[blue]agent {job.next_step.code}[/blue].")
                print(Rule("Summary"))
                for s in job.next_step.completed_steps_laconic:
                    print(f"- {s}")
                print(Rule())
                break

            # let's be nice and print the next remaining step (discard all others)
            print(job.plan_remaining_steps[0], f"\n  {job.next_step}")

            # Let's add tool request to conversation history as if OpenAI asked for it.
            # a shorter way would be to just append `job.model_dump_json()` entirely
            log.append({
                "role": "assistant",
                #"content" : job.next_step_to_execute.model_dump_json()
                #"content": job.plan_remaining_steps_brief[0],
                "content" : job.next_step.tool,
                "tool_call": {
                    "name": job.next_step.tool,
                    "arguments": job.next_step.model_dump_json(),
                }
            })

            # now execute the tool by dispatching command to our handler
            result = dispatch(job.next_step)
            txt = result if isinstance(result, str) else json.dumps(result)
            #print("OUTPUT", result)
            # and now we add results back to the convesation history, so that agent
            # we'll be able to act on the results in the next reasoning step.
            log.append({"role": "tool", "name" : job.next_step.tool, "content": txt })

if __name__ == "__main__":
    execute_tasks()