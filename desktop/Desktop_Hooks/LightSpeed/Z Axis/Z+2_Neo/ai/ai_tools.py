"""
AI Tools - LightSpeed Platform
External API integrations for AI assistant capabilities

Tools:
- nullschool: Earth wind/weather data visualization
- Tree of Life: Biodiversity and taxonomy data
- QR Code Generation: QR code creation
"""

import requests
import qrcode
from io import BytesIO
from typing import Dict, Any, Optional
from pathlib import Path


class AITools:
    """Collection of AI-accessible tools for enhanced assistant capabilities."""

    @staticmethod
    def get_wind_data(lat: float = 35.0, lon: float = -95.0) -> Dict[str, Any]:
        """
        Get wind and weather data from nullschool Earth API.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Weather data dictionary
        """
        try:
            # Nullschool uses a specific API format
            # This is a simplified version - actual API may vary
            url = f"https://earth.nullschool.net/api/weather/{lat}/{lon}"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'data': data,
                    'location': {'lat': lat, 'lon': lon}
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'message': 'Weather data unavailable'
                }

        except requests.Timeout:
            return {'success': False, 'error': 'Timeout', 'message': 'Request timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'message': 'Failed to fetch weather data'}

    @staticmethod
    def search_tree_of_life(query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Search Open Tree of Life taxonomy database.

        Args:
            query: Scientific or common name
            limit: Max results

        Returns:
            Taxonomy search results
        """
        try:
            url = "https://api.opentreeoflife.org/v3/tnrs/match_names"

            payload = {
                "names": [query],
                "do_approximate_matching": True
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])

                if results:
                    matches = results[0].get('matches', [])[:limit]
                    return {
                        'success': True,
                        'query': query,
                        'matches': [
                            {
                                'name': m.get('matched_name', 'Unknown'),
                                'unique_name': m.get('taxon', {}).get('unique_name', ''),
                                'rank': m.get('taxon', {}).get('rank', ''),
                                'ott_id': m.get('taxon', {}).get('ott_id', 0)
                            }
                            for m in matches
                        ]
                    }
                else:
                    return {
                        'success': False,
                        'query': query,
                        'message': 'No matches found'
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'message': 'Tree of Life API unavailable'
                }

        except Exception as e:
            return {'success': False, 'error': str(e), 'message': 'Failed to search Tree of Life'}

    @staticmethod
    def generate_qr_code(
        data: str,
        output_path: Optional[Path] = None,
        size: int = 10,
        border: int = 2
    ) -> Dict[str, Any]:
        """
        Generate QR code from text/URL.

        Args:
            data: Text or URL to encode
            output_path: Optional path to save PNG (if None, returns base64)
            size: QR code size (default 10)
            border: Border size in boxes (default 2)

        Returns:
            QR code generation result
        """
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=border
            )

            qr.add_data(data)
            qr.make(fit=True)

            # Generate image
            img = qr.make_image(fill_color="black", back_color="white")

            if output_path:
                # Save to file
                img.save(output_path)
                return {
                    'success': True,
                    'output_path': str(output_path),
                    'data_length': len(data)
                }
            else:
                # Return base64 encoded
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                import base64
                img_str = base64.b64encode(buffered.getvalue()).decode()

                return {
                    'success': True,
                    'base64': img_str,
                    'data_length': len(data)
                }

        except Exception as e:
            return {'success': False, 'error': str(e), 'message': 'Failed to generate QR code'}

    @staticmethod
    def format_tool_response(tool_name: str, result: Dict[str, Any]) -> str:
        """
        Format tool response for AI conversation.

        Args:
            tool_name: Name of the tool
            result: Tool result dictionary

        Returns:
            Formatted response string
        """
        if tool_name == "wind_data":
            if result.get('success'):
                data = result.get('data', {})
                return f"Wind/Weather data for ({result['location']['lat']}, {result['location']['lon']}): {data}"
            else:
                return f"Weather data unavailable: {result.get('message', 'Unknown error')}"

        elif tool_name == "tree_of_life":
            if result.get('success'):
                matches = result.get('matches', [])
                if matches:
                    response = f"Tree of Life search for '{result['query']}':\n"
                    for i, match in enumerate(matches, 1):
                        response += f"{i}. {match['name']} ({match['rank']})\n"
                    return response
                else:
                    return f"No matches found for '{result['query']}'"
            else:
                return f"Tree of Life search failed: {result.get('message', 'Unknown error')}"

        elif tool_name == "qr_code":
            if result.get('success'):
                if 'output_path' in result:
                    return f"QR code generated: {result['output_path']}"
                else:
                    return f"QR code generated (base64, {result['data_length']} bytes encoded)"
            else:
                return f"QR code generation failed: {result.get('message', 'Unknown error')}"

        else:
            return f"Tool '{tool_name}' response: {result}"


# Example usage for AI integration
def demo_tools():
    """Demonstrate AI tools."""
    tools = AITools()

    print("=== AI Tools Demo ===\n")

    # Wind data
    print("1. Wind/Weather Data:")
    wind_result = tools.get_wind_data(35.0, -95.0)
    print(tools.format_tool_response("wind_data", wind_result))
    print()

    # Tree of Life
    print("2. Tree of Life Search:")
    tree_result = tools.search_tree_of_life("panthera leo")
    print(tools.format_tool_response("tree_of_life", tree_result))
    print()

    # QR Code
    print("3. QR Code Generation:")
    qr_result = tools.generate_qr_code("https://lightspeed.com", output_path=Path("test_qr.png"))
    print(tools.format_tool_response("qr_code", qr_result))


if __name__ == "__main__":
    demo_tools()
