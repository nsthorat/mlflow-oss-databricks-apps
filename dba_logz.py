#!/usr/bin/env python3
"""Simple SSE client for Databricks App logs."""

import json
import os
import subprocess
import time
from typing import Optional

import requests
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')


class LogzClient:
  """Client for streaming logs from Databricks App /logz/stream endpoint."""

  def __init__(self, app_url: str):
    self.app_url = app_url.rstrip('/')
    self.sse_url = self.app_url + '/logz/stream'
    self._token_cache = None

  def _get_oauth_token(self) -> str:
    """Get OAuth token using Databricks CLI."""
    try:
      profile = os.getenv('DATABRICKS_CONFIG_PROFILE')
      host = os.getenv('DATABRICKS_HOST')

      cmd = ['databricks', 'auth', 'token']

      if profile:
        cmd.extend(['--profile', profile])
      elif host:
        cmd.extend(['--host', host])
      else:
        raise Exception(
          'Neither DATABRICKS_CONFIG_PROFILE nor DATABRICKS_HOST environment variable is set'
        )

      result = subprocess.run(cmd, capture_output=True, text=True, check=True)
      token_output = result.stdout.strip()
      
      try:
        token_data = json.loads(token_output)
        return token_data.get('access_token', token_output)
      except json.JSONDecodeError:
        return token_output

    except subprocess.CalledProcessError as e:
      raise Exception(f'Failed to get OAuth token: {e}')
    except FileNotFoundError:
      raise Exception('databricks CLI not found. Please install databricks CLI.')

  def stream_logs(self, search_query: str = '', duration: int = 30):
    """Stream logs using Server-Sent Events (SSE).
    
    Args:
        search_query: Optional search query to filter logs
        duration: How long to stream logs in seconds (0 = forever)
    """
    if not self._token_cache:
      self._token_cache = self._get_oauth_token()
    
    headers = {
      'Authorization': f'Bearer {self._token_cache}',
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
    }
    
    # Build URL with query parameter
    params = {}
    if search_query:
      params['q'] = search_query
    
    print(f'Connecting to: {self.sse_url}')
    if search_query:
      print(f"Search query: '{search_query}'")
    if duration > 0:
      print(f'Streaming for {duration} seconds...')
    else:
      print('Streaming continuously (Ctrl+C to stop)...')
    print('-' * 50)
    
    try:
      # Make streaming request
      response = requests.get(
        self.sse_url,
        headers=headers,
        params=params,
        stream=True,
        timeout=(5, None if duration == 0 else duration)
      )
      
      if response.status_code != 200:
        print(f'❌ Failed to connect: HTTP {response.status_code}')
        if response.status_code == 503:
          print('   The app may be starting up. Try again in a few seconds.')
        elif 'oidc' in response.text.lower():
          print('   Authentication required. Please login via browser first.')
        return
      
      print('✅ Connected successfully!')
      print('📋 Streaming logs...\n')
      
      start_time = time.time()
      message_count = 0
      
      # Process the SSE stream  
      buffer = ""
      for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if duration > 0 and time.time() - start_time > duration:
          break
          
        if chunk:
          buffer += chunk
          
          # Process complete lines
          while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            
            if not line:
              continue
              
            # SSE format: data: {json}
            if line.startswith('data: '):
              data = line[6:]  # Remove 'data: ' prefix
              
              # Handle null byte as "no logs" indicator
              if data == '\x00':
                if message_count == 0:
                  print('📭 No logs available yet')
              else:
                message_count += 1
                try:
                  log_entry = json.loads(data)
                  timestamp = log_entry.get('timestamp', '')
                  source = log_entry.get('source', 'UNKNOWN')
                  msg = log_entry.get('message', '')
                  
                  # Format timestamp if present
                  if timestamp:
                    from datetime import datetime
                    dt = datetime.fromtimestamp(timestamp)
                    timestamp_str = dt.strftime('%H:%M:%S')
                  else:
                    timestamp_str = '        '
                  
                  # Color code by source
                  if source == 'SYSTEM':
                    source_str = 'SYSTEM'
                  elif source == 'APP':
                    source_str = 'APP   '
                  else:
                    source_str = source[:6].ljust(6)
                  
                  print(f'[{timestamp_str}] {source_str}: {msg}')
                  
                except json.JSONDecodeError:
                  # Not JSON, print as-is
                  print(f'📋 {data}')
      
      if duration > 0:
        print(f'\n⏰ Completed after {duration} seconds')
      print(f'📊 Received {message_count} log messages')
        
    except requests.exceptions.Timeout:
      print(f'\n⏰ Streaming timeout reached')
    except KeyboardInterrupt:
      print(f'\n⏹️  Stopped by user')
    except Exception as e:
      print(f'❌ Error: {e}')


def main():
  """CLI interface for the logz client."""
  import argparse

  parser = argparse.ArgumentParser(
    description='Stream logs from Databricks App',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Stream logs for 30 seconds
  python dba_logz.py https://app.databricksapps.com
  
  # Stream logs continuously
  python dba_logz.py https://app.databricksapps.com --duration 0
  
  # Search for ERROR messages
  python dba_logz.py https://app.databricksapps.com --search ERROR
  
  # Search for specific text for 60 seconds
  python dba_logz.py https://app.databricksapps.com --search "database" --duration 60
    """
  )
  parser.add_argument('app_url', help='Base URL of the Databricks app')
  parser.add_argument('--search', default='', help='Search query to filter logs')
  parser.add_argument('--duration', type=int, default=30, 
                      help='How long to stream logs in seconds (0 = forever)')

  args = parser.parse_args()

  client = LogzClient(args.app_url)
  client.stream_logs(args.search, args.duration)


if __name__ == '__main__':
  main()