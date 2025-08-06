from core.claude import Claude
from mcp_client import MCPClient
from core.tools import ToolManager
from anthropic.types import MessageParam


class Chat:
    def __init__(self, claude_service: Claude, clients: dict[str, MCPClient]):
        self.claude_service: Claude = claude_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list[MessageParam] = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    async def run(self, query: str) -> str:
        
        final_text_response = ""
        
        await self._process_query(query)
        
        # Debug: Check what tools are being passed
        tools = await ToolManager.get_all_tools(self.clients)
        print(f"DEBUG: Passing {len(tools)} tools to Claude:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        while True:
            response = self.claude_service.chat(
                messages=self.messages,
                tools=tools,  # Use the cached tools
            )
            
            # Debug: Check Claude's response
            print(f"DEBUG: Claude's stop_reason: {response.stop_reason}")
            if hasattr(response, 'content'):
                print(f"DEBUG: Response content type: {type(response.content)}")
            
            self.claude_service.add_assistant_message(self.messages, response)
            
            if response.stop_reason == "tool_use":
                print("DEBUG: Claude wants to use a tool!")
                print(self.claude_service.text_from_message(response))
                tool_result_parts = await ToolManager.execute_tool_requests(
                    self.clients, response
                )
                
                self.claude_service.add_user_message(
                    self.messages, tool_result_parts
                )
            else:
                final_text_response = self.claude_service.text_from_message(response)
                break
        
        return final_text_response
