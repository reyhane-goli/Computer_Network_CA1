import json
import socket
import os
import sys

class FTPclient:
	def __init__(self, address, port, data_port, conf_dict):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.address = address
		self.port = int(port)
		self.data_port = int(data_port)
		self.conf_dict = conf_dict

	def create_connection(self):
	  print ('Starting connection to', self.address, ':', self.port)

	  try:
	  	server_address = (self.address, self.port)
	  	self.sock.connect(server_address)
	  	print ('Connected to', self.address, ':', self.port)
	  except KeyboardInterrupt:
	  	self.close_client()
	  except:
	  	print ('Connection to', self.address, ':', self.port, 'failed')
	  	self.close_client()

	def start(self):
		try:
			self.create_connection()
		except Exception as e:
			self.close_client()

		while True:
			try:
				command = input('Enter command: ')
				if not command: 
					print ('Need a command.')
					continue
			except KeyboardInterrupt:
				self.close_client()

			if command[:2].strip().upper()=='DL':
				cmd  = command[:2].strip().upper()
				path = command[2:].strip()
			else:
				cmd  = command[:4].strip().upper()
				path = command[4:].strip()


			try:
				self.sock.sendall(command.encode('utf-8'))
				data_rec = self.sock.recv(1024)
				data=str(data_rec.decode('utf-8'))
				print (data)

				if (cmd == 'QUIT'):
					self.close_client()
				elif (cmd == 'LIST'  or cmd == 'DL'):
					if (data and (data[0:3] == '125')):
						func = getattr(self, cmd)
						func(path)
						data = self.sock.recv(1024)
						print (str(data.decode('utf-8')))
			except Exception as e:
				print (str(e))
				self.close_client()

	def connect_datasock(self):
		try:
			self.datasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.datasock.connect((self.address, self.data_port))
		except Exception as e:
			print (str(e))

	def LIST(self, path):
		try:
			self.connect_datasock()
			while True:
				dirlist = self.datasock.recv(1024)
				if not dirlist: break
				sys.stdout.write(str(dirlist.decode('utf-8')))
				sys.stdout.flush()
		except Exception as e:
			print (str(e))
		finally:
			self.datasock.close()

	def DL(self, path):
		print ('Downloading', path, 'from the server')
		try: 
			self.connect_datasock()
			f = open(path,'w')
			while True:
				download = self.datasock.recv(1024)
				if not download: break
				f.write(str(download.decode('utf-8')))
		except Exception as e:
			print (str(e))
		finally:
			f.close()
			self.datasock.close()

	def close_client(self):
		print ('Closing socket connection...')
		self.sock.close()

		print ('FTP client terminating...')
		quit()


address = '127.0.0.1'
with open('config.json', 'r') as conf:
    conf_dict = json.load(conf)
port = conf_dict['commandChannelPort']
data_port = conf_dict['dataChannelPort']

ftpClient = FTPclient(address, port, data_port, conf_dict)
ftpClient.start()
