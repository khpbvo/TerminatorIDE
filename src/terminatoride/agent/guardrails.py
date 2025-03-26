"""
Guardrails for TerminatorIDE agents.
These guardrails help ensure safe and responsible agent interactions.
"""
from typing import Dict, Any, Optional, List, Union, Tuple
from pydantic import BaseModel
from agents import (
    Agent, RunContextWrapper, GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered,
    Runner, TResponseInputItem, input_guardrail, output_guardrail
)

class CodeInjectionResult(BaseModel):
    """Result of a code injection check."""
    is_injection_attempt: bool
    risk_level: str  # "low", "medium", "high"
    reasoning: str

class ShellCommandResult(BaseModel):
    """Result of a shell command safety check."""
    is_dangerous: bool
    risk_level: str  # "low", "medium", "high"
    reasoning: str

class ModerationResult(BaseModel):
    """Result of a content moderation check."""
    is_inappropriate: bool
    categories: List[str]
    reasoning: str

# Guardrail agents for different checks
code_injection_agent = Agent(
    name="Code Injection Checker",
    instructions="""
    You are a security agent that detects code injection attempts in user inputs.
    Analyze the input for attempts to:
    1. Inject malicious code into Python execution functions
    2. Execute harmful shell commands
    3. Access sensitive system files or resources
    4. Exploit vulnerabilities in the IDE
    
    Provide a detailed reasoning for your decision, rating the risk level as low, medium, or high.
    """,
    output_type=CodeInjectionResult,
    model="o3-mini",  # Using a smaller model for efficiency
)

shell_command_agent = Agent(
    name="Shell Command Safety Checker",
    instructions="""
    You are a security agent that evaluates the safety of shell commands.
    Analyze the command for:
    1. System-destructive operations (rm -rf, format, etc.)
    2. Network attacks or exploits
    3. Attempts to access sensitive files or data
    4. Execution of malicious scripts or programs
    
    Provide a detailed reasoning for your decision, rating the risk level as low, medium, or high.
    """,
    output_type=ShellCommandResult,
    model="o3-mini",
)

moderation_agent = Agent(
    name="Content Moderation Agent",
    instructions="""
    You are a content moderation agent that checks if user inputs contain inappropriate content.
    Look for content related to:
    1. Harmful instructions or illegal activities
    2. Offensive language or hate speech
    3. Adult or NSFW content
    4. Personal or sensitive information requests
    
    Categorize any violations and explain your reasoning.
    """,
    output_type=ModerationResult,
    model="o3-mini",
)

# Dangerous file paths that should not be accessed
RESTRICTED_PATHS = [
    "/etc/passwd",
    "/etc/shadow",
    "/etc/ssh",
    "/.ssh",
    "/root",
    "/var/log",
    "C:\\Windows\\System32",
    "C:\\Users\\Administrator",
    "~/.aws",
    "~/.ssh",
]

# Dangerous shell commands
DANGEROUS_COMMANDS = [
    "rm -rf /",
    "rm -rf /*",
    "rm -rf ~",
    "rm -rf .",
    ":(){ :|:& };:",  # Fork bomb
    "dd if=/dev/random",
    "mkfs",
    "format",
    "> /dev/sda",
    "chmod -R 777 /",
]

# Input guardrail for code injection detection
@input_guardrail
async def detect_code_injection(
    ctx: RunContextWrapper[Any], agent: Agent, input: Union[str, List[TResponseInputItem]]
) -> GuardrailFunctionOutput:
    """
    Detect potential code injection attempts in user input.
    
    Args:
        ctx: The run context wrapper
        agent: The agent being used
        input: The user input to check
    
    Returns:
        GuardrailFunctionOutput with detection results
    """
    # Convert input to string if it's a list
    input_text = input if isinstance(input, str) else str(input)
    
    # Basic pattern checks (quick first pass)
    # Check for suspicious Python patterns
    python_patterns = [
        "exec(", "eval(", "os.system(", "subprocess", "import os;", 
        "__import__", "open(", "file =", "with open"
    ]
    
    # Check for suspicious shell patterns
    shell_patterns = [
        "rm -rf", "> /dev/", "sudo", "chmod 777", "|", ";", "&&", 
        "wget", "curl", "> /etc/"
    ]
    
    # Quick check for obviously dangerous inputs
    for pattern in python_patterns + shell_patterns:
        if pattern in input_text.lower():
            # If basic pattern detected, get a more thorough analysis
            result = await Runner.run(code_injection_agent, input_text, context=ctx.context)
            output = result.final_output
            
            # Only trigger on medium or high risk
            return GuardrailFunctionOutput(
                output_info=output,
                tripwire_triggered=output.is_injection_attempt and output.risk_level in ["medium", "high"]
            )
    
    # Check for restricted paths
    for path in RESTRICTED_PATHS:
        if path in input_text:
            return GuardrailFunctionOutput(
                output_info=CodeInjectionResult(
                    is_injection_attempt=True,
                    risk_level="high",
                    reasoning=f"Attempt to access restricted path: {path}"
                ),
                tripwire_triggered=True
            )
    
    # If no basic patterns found, it's probably safe
    return GuardrailFunctionOutput(
        output_info=CodeInjectionResult(
            is_injection_attempt=False,
            risk_level="low",
            reasoning="No suspicious patterns detected in user input"
        ),
        tripwire_triggered=False
    )

# Input guardrail for shell command safety
@input_guardrail
async def check_shell_command_safety(
    ctx: RunContextWrapper[Any], agent: Agent, input: Union[str, List[TResponseInputItem]]
) -> GuardrailFunctionOutput:
    """
    Check if input contains dangerous shell commands.
    
    Args:
        ctx: The run context wrapper
        agent: The agent being used
        input: The user input to check
    
    Returns:
        GuardrailFunctionOutput with safety check results
    """
    # Convert input to string if it's a list
    input_text = input if isinstance(input, str) else str(input)
    
    # Check for exactly matching dangerous commands
    for cmd in DANGEROUS_COMMANDS:
        if cmd in input_text:
            return GuardrailFunctionOutput(
                output_info=ShellCommandResult(
                    is_dangerous=True,
                    risk_level="high",
                    reasoning=f"Input contains known dangerous command: {cmd}"
                ),
                tripwire_triggered=True
            )
    
    # For more nuanced analysis, use the shell command agent
    if any(cmd in input_text.lower() for cmd in ["rm", "sudo", "chmod", "chown", "dd", ">", "|", "&"]):
        result = await Runner.run(shell_command_agent, input_text, context=ctx.context)
        output = result.final_output
        
        return GuardrailFunctionOutput(
            output_info=output,
            tripwire_triggered=output.is_dangerous and output.risk_level in ["medium", "high"]
        )
    
    # If no suspicious patterns found, it's probably safe
    return GuardrailFunctionOutput(
        output_info=ShellCommandResult(
            is_dangerous=False,
            risk_level="low",
            reasoning="No dangerous shell commands detected"
        ),
        tripwire_triggered=False
    )

# Input guardrail for content moderation
@input_guardrail
async def moderate_content(
    ctx: RunContextWrapper[Any], agent: Agent, input: Union[str, List[TResponseInputItem]]
) -> GuardrailFunctionOutput:
    """
    Moderate user input for inappropriate content.
    
    Args:
        ctx: The run context wrapper
        agent: The agent being used
        input: The user input to check
    
    Returns:
        GuardrailFunctionOutput with moderation results
    """
    # Convert input to string if it's a list
    input_text = input if isinstance(input, str) else str(input)
    
    # Use moderation agent for content analysis
    result = await Runner.run(moderation_agent, input_text, context=ctx.context)
    output = result.final_output
    
    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=output.is_inappropriate
    )

# Output guardrail to ensure safe responses
@output_guardrail
async def ensure_safe_output(
    ctx: RunContextWrapper[Any], agent: Agent, output: Any
) -> GuardrailFunctionOutput:
    """
    Ensure agent output is safe and doesn't contain harmful content.
    
    Args:
        ctx: The run context wrapper
        agent: The agent being used
        output: The agent output to check
    
    Returns:
        GuardrailFunctionOutput with safety check results
    """
    # Convert output to string for checking
    output_text = str(output)
    
    # Check for dangerous commands in the output
    for cmd in DANGEROUS_COMMANDS:
        if cmd in output_text:
            return GuardrailFunctionOutput(
                output_info=ShellCommandResult(
                    is_dangerous=True,
                    risk_level="high",
                    reasoning=f"Output contains dangerous command: {cmd}"
                ),
                tripwire_triggered=True
            )
    
    # Check for restricted paths in the output
    for path in RESTRICTED_PATHS:
        if path in output_text:
            return GuardrailFunctionOutput(
                output_info=CodeInjectionResult(
                    is_injection_attempt=True,
                    risk_level="high",
                    reasoning=f"Output contains restricted path: {path}"
                ),
                tripwire_triggered=True
            )
    
    # If output looks safe
    return GuardrailFunctionOutput(
        output_info="Output appears safe",
        tripwire_triggered=False
    )

def get_default_guardrails() -> Tuple[List, List]:
    """
    Get the default input and output guardrails.
    
    Returns:
        Tuple of (input_guardrails, output_guardrails)
    """
    return (
        [detect_code_injection, check_shell_command_safety, moderate_content],
        [ensure_safe_output]
    )