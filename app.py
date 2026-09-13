from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading
import cgi
from urllib.parse import parse_qs
import json
import base64

class FileUploadHandler(SimpleHTTPRequestHandler):
    latest_message = ""
    audio_clients = []  # Store connected audio clients
    current_audio_stream = None
    audio_buffer = []

    def do_POST(self):
        content_type, _ = cgi.parse_header(self.headers['Content-Type'])
        print(f"Content type: {content_type}")

        if content_type == 'application/x-www-form-urlencoded':
            length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(length)
            data = parse_qs(post_data.decode('utf-8'))

            if "message" in data:
                message = data["message"][0]

                # Handle the received message as needed
                print(f"Received message: {message}")

                # Store the latest message
                FileUploadHandler.latest_message = message

                # Send a response to the client
                self.send_response(200)
                self.end_headers()
                self.wfile.write(bytes(f"Message received: {message}", "utf-8"))
        elif content_type == 'application/json':
            # Handle streaming audio data
            length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                print(f"Received JSON data: {data.get('type', 'unknown')}")  # Debug output
                
                if data.get('type') == 'audio_chunk':
                    # Store audio chunk for Unity clients
                    audio_data = base64.b64decode(data['audio_data'])
                    FileUploadHandler.broadcast_audio_chunk(audio_data, data.get('sample_rate', 22050))
                    
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'Audio chunk received')
                elif data.get('type') == 'audio_start':
                    # Signal start of new audio stream
                    FileUploadHandler.audio_buffer = []
                    FileUploadHandler.broadcast_audio_start(data.get('sample_rate', 22050))
                    
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'Audio stream started')
                elif data.get('type') == 'audio_end':
                    # Signal end of audio stream
                    FileUploadHandler.broadcast_audio_end()
                    
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'Audio stream ended')
                elif data.get('type') == 'animation_command':
                    # Handle animation command
                    animation_name = data.get('animation', 'unknown')
                    print(f"🎭 Received animation command: {animation_name}")
                    FileUploadHandler.broadcast_animation_command(animation_name)
                    
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'Animation command received')
                elif data.get('type') == 'face_position':
                    # Handle face tracking data from face_tracker.py
                    motor_position = data.get('motor_position', 0.0)
                    x = data.get('x', 0.5)
                    y = data.get('y', 0.5)
                    servo_angle = data.get('servo_angle', 120.0)
                    detected = data.get('detected', False)
                    FileUploadHandler.broadcast_face_position(motor_position, x, y, servo_angle, detected)
                    
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'Face position received')
                else:
                    print(f"Unknown message type: {data.get('type')}")  # Debug output
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'Unknown message type')
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")  # Debug output
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Invalid JSON')
            except Exception as e:
                print(f"Error processing audio data: {e}")  # Debug output
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'Server error')
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(bytes("Invalid content type", "utf-8"))

    def do_GET(self):
        # Normalize path to handle double slashes
        normalized_path = self.path.replace('//', '/')
        print(f"🌐 GET request: {self.path} -> {normalized_path} from {self.client_address}")
        
        if normalized_path == "/latest_message":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Convert the latest_message to string before writing to the socket
            self.wfile.write(str(self.latest_message).encode('utf-8'))
        elif normalized_path == "/audio_stream":
            # WebSocket-like connection for audio streaming
            print(f"🎵 Unity client connecting to audio stream from {self.client_address}")
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            
            # Add this client to audio clients
            FileUploadHandler.audio_clients.append(self)
            print(f"🎵 Added client to audio stream (Total clients: {len(FileUploadHandler.audio_clients)})")
            
            # Keep connection alive
            try:
                while True:
                    # Send heartbeat every 30 seconds
                    self.wfile.write(b'heartbeat\n')
                    self.wfile.flush()
                    threading.Event().wait(30)
            except Exception as e:
                print(f"🎵 Client disconnected: {e}")
                # Client disconnected
                if self in FileUploadHandler.audio_clients:
                    FileUploadHandler.audio_clients.remove(self)
                    print(f"🎵 Removed client from audio stream (Remaining clients: {len(FileUploadHandler.audio_clients)})")
        elif normalized_path == "/audio_status":
            # Get current audio streaming status
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            status = {
                'streaming': self.current_audio_stream is not None,
                'buffer_size': len(self.audio_buffer)
            }
            self.wfile.write(json.dumps(status).encode('utf-8'))
        else:
            # Handle unknown paths with proper 404 response
            print(f"⚠️ Unknown path requested: {self.path}")
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"404 - Path not found: {self.path}".encode('utf-8'))

    @classmethod
    def broadcast_audio_chunk(cls, audio_data, sample_rate=22050):
        """Broadcast audio chunk to all connected Unity clients"""
        print(f"🎵 Broadcasting audio chunk to {len(cls.audio_clients)} clients")
        
        # Convert audio data to base64 for JSON transmission
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            'type': 'audio_chunk',
            'audio_data': audio_b64,
            'sample_rate': sample_rate,
            'timestamp': threading.Event().wait(0)  # Current time
        }
        
        cls._broadcast_message(message)
        
        # Also store in buffer for late-joining clients
        cls.audio_buffer.append(audio_data)
        
        # Limit buffer size (keep last 5 seconds worth)
        max_buffer_size = sample_rate * 5  # 5 seconds
        total_samples = sum(len(chunk) // 4 for chunk in cls.audio_buffer)  # Assuming 32-bit float
        while total_samples > max_buffer_size and cls.audio_buffer:
            removed_chunk = cls.audio_buffer.pop(0)
            total_samples -= len(removed_chunk) // 4
    
    @classmethod
    def broadcast_audio_start(cls, sample_rate=22050):
        """Signal start of new audio stream"""
        print(f"🎵 Broadcasting audio start to {len(cls.audio_clients)} clients")
        message = {
            'type': 'audio_start',
            'sample_rate': sample_rate
        }
        cls._broadcast_message(message)
    
    @classmethod
    def broadcast_audio_end(cls):
        """Signal end of audio stream"""
        print(f"🎵 Broadcasting audio end to {len(cls.audio_clients)} clients")
        message = {
            'type': 'audio_end'
        }
        cls._broadcast_message(message)
        cls.audio_buffer = []
    
    @classmethod
    def broadcast_animation_command(cls, animation_name):
        """Send animation command to all connected Unity clients"""
        print(f"🎭 Broadcasting animation command '{animation_name}' to {len(cls.audio_clients)} clients")
        message = {
            'type': 'animation_command',
            'audio_data': animation_name,  # Using audio_data field for animation name
            'sample_rate': 0,  # Not used for animations
            'timestamp': 0     # Not used for animations
        }
        cls._broadcast_message(message)
    
    @classmethod
    def broadcast_face_position(cls, motor_position, x, y, servo_angle, detected):
        """Send face position to all connected Unity clients for camera orbit"""
        message = {
            'type': 'face_position',
            'motor_position': motor_position,
            'x': x,
            'y': y,
            'servo_angle': servo_angle,
            'detected': detected
        }
        cls._broadcast_message(message)
    
    @classmethod
    def _broadcast_message(cls, message):
        """Send message to all connected audio clients"""
        message_str = json.dumps(message) + '\n'
        print(f"🎵 Sending message to {len(cls.audio_clients)} clients: {message['type']}")
        disconnected_clients = []
        
        for client in cls.audio_clients:
            try:
                client.wfile.write(message_str.encode('utf-8'))
                client.wfile.flush()
            except Exception as e:
                print(f"🎵 Failed to send to client: {e}")
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            if client in cls.audio_clients:
                cls.audio_clients.remove(client)
                print(f"🎵 Removed disconnected client (Remaining: {len(cls.audio_clients)})")

def start_server():
    server_address = ('0.0.0.0', 8000)
    httpd = ThreadingHTTPServer(server_address, FileUploadHandler)

    print('🚀 Server started on port 8000...')
    print('📡 Audio streaming endpoint: http://localhost:8000/audio_stream')
    print('📝 Latest message endpoint: http://localhost:8000/latest_message')
    print('📊 Audio status endpoint: http://localhost:8000/audio_status')
    print('💾 Listening on all interfaces (0.0.0.0:8000)')
    httpd.serve_forever()

if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    input("Press Enter to stop server...\n")
