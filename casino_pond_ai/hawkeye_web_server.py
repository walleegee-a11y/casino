#!/usr/local/bin/python3.12
"""
Hawkeye Web Server - Main Entry Point
Provides REST API and web interface for CASINO Hawkeye analysis data
"""

import os
import argparse
from hawkeye_web_server.core import create_app, discover_projects
from hawkeye_web_server.config import Config


def main():
    """Run the web server"""
    parser = argparse.ArgumentParser(description="Hawkeye Web Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5021, help='Port to bind to (default: 5021)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    # Update config if custom host/port specified
    if args.host != '0.0.0.0':
        Config.HOST = args.host
    if args.port != 5021:
        Config.PORT = args.port
    if args.debug:
        Config.DEBUG = args.debug

    # Print startup information
    print("=" * 60)
    print("Starting Hawkeye Web Server...")
    print("=" * 60)
    print(f"casino_prj_base: {os.getenv('casino_prj_base', 'Not set')}")
    print(f"Server URL: http://{args.host}:{args.port}")
    print(f"Project Selector: http://{args.host}:{args.port}/select-project")
    print(f"Debug Mode: {'Enabled' if args.debug else 'Disabled'}")

    # Discover available projects
    projects = discover_projects()
    print(f"Found {len(projects)} project(s)")
    for project in projects:
        if project['has_archive']:
            print(f"   [+] {project['name']} ({project['run_count']} runs)")
        else:
            print(f"   [-] {project['name']} (no archive)")

    print("=" * 60)

    # Create and run Flask app
    app = create_app(Config)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
