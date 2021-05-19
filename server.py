import json
import socket
import os
import sys
import threading
import time
import logging
import datetime
import base64
import getpass
import ssl

class FTPThreadServer(threading.Thread):
	def __init__(self, client, client_address, local_ip, data_port, conf_dict, log_en):
		self.client = client
		self.client_address = client_address
		self.cwd = os.getcwd()
		self.data_address = (local_ip, data_port)
		self.conf_dict = conf_dict
		self.auth = 0
		self.log_en = log_en
		self.first_cwd=os.getcwd()
		threading.Thread.__init__(self)

	def start_datasock(self):
		try:
			print ('Creating data socket on' + str(self.data_address) + '...')
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.info(now + ' : Creating data socket on')
			
			self.datasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.datasock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

			self.datasock.bind(self.data_address)
			self.datasock.listen(5)
			
			print ('Data socket is started. Listening to' + str(self.data_address) + '...')
			message='125 Data connection already open; transfer starting.\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.info(now + ' : Data socket is started. Listening to')
				logging.info(now + ' : ' + message)

			return self.datasock.accept()
		except Exception as e:
			print ('500 ERROR: test ' + str(self.client_address) + ': ' + str(e))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : 500 ERROR')
			self.close_datasock()
			message='425 Cannot open data connection.\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' +  message)

	def close_datasock(self):
		print ('Closing data socket connection...')
		if self.log_en==True:
			now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			logging.info(now + ' : Closing data socket connection...')
		try:
			self.datasock.close()
		except:
			pass

	def run(self):
		try :
			print ('client connected: ' + str(self.client_address) + '\n')
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.info(now + ' : client connected')

			while True:
				cmd_rec = self.client.recv(1024)
				cmd = str(cmd_rec.decode('utf-8'))
				if not cmd_rec: break
				print ('commands from ' + str(self.client_address) + ': ' + cmd)
				message='commands from ' + str(self.client_address) + ': ' + cmd
				if self.log_en==True:
					now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					logging.info(now + ' : ' + message)
				try:
					if cmd[:2].strip().upper()=='DL':
						func = getattr(self, cmd[:2].strip().upper())
						func(cmd)
					else:
						func = getattr(self, cmd[:4].strip().upper())
						func(cmd)
				except AttributeError as e:
					print ('ERROR: ' + str(self.client_address) + ': Invalid Command.')
					message='550 Invalid Command\r\n'
					self.client.sendall(message.encode('utf-8'))
					if self.log_en==True:
						now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						logging.error(now + ' : ERROR: Invalid Command.')
						logging.error(now + ' : ' + message)
		except Exception as e:
			print ('500 ERROR: ' + str(self.client_address) + ': ' + str(e))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : 500 ERROR')
			self.QUIT('')

	def USER(self, cmd):
		global username
		username = cmd[4:].strip()
		find = False
		for i in range(0,len(self.conf_dict['users'])):
			if username == conf_dict['users'][i]['user']:
				message='331 ‫‪User‬‬ ‫‪name‬‬ ‫‪okay,‬‬ ‫‪need‬‬ ‫‪password.‬‬\r\n'
				self.client.sendall(message.encode('utf-8'))
				if self.log_en==True:
					now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					logging.info(now + ' : ' + message)
				find = True
				self.auth = 1
		if find == False:
			message='‫‪430‬‬ ‫‪Invalid‬‬ ‫‪username‬‬ ‫‪or‬‬ ‫‪password.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' + message)

	def PASS(self, cmd):
		password = cmd[4:].strip()
		find = False
		if self.auth == 0:
			message='503‬‬ ‫‪Bad‬‬ ‫‪sequence‬‬ ‫‪of‬‬ ‫‪commands.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' + message)
			return
		for i in range(0,len(self.conf_dict['users'])):
			if password == conf_dict['users'][i]['password']:
				message='‫‪230‬‬ ‫‪User‬‬ ‫‪logged‬‬ ‫‪in,‬‬ ‫‪proceed.‬‬\r\n'
				self.client.sendall(message.encode('utf-8'))
				if self.log_en==True:
					now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					logging.info(now + ' : ' + message)
				find=True
				self.auth = 2
		if find == False:
			message='‫‪430‬‬ ‫‪Invalid‬‬ ‫‪username‬‬ ‫‪or‬‬ ‫‪password.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' + message)

	def check_auth(self):
		if self.auth!=2:
			return False
		else:
			return True

	def send_email(self,index):
		mailserv = 'mail.ut.ac.ir'
		mailport = 465
		mailfrom = 'yasamin.rahimi.s@ut.ac.ir'
		mailrcpt = conf_dict['accounting']['users'][index]['email']
		mailmess = 'Hi\nYour remaining space is less than threshold!\nFTPServer'
		username = 'yasamin.rahimi.s'
		password = 'Ry002996'
		sock = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), ssl_version=ssl.PROTOCOL_SSLv23)
		sock.connect((mailserv, mailport))
		respon = sock.recv(2048)
		print(str(respon, 'utf-8'))
		heloMesg = 'HELO Yasamin\r\n'
		print(heloMesg)
		sock.send(heloMesg.encode('utf-8'))
		respon = sock.recv(2048)
		print(str(respon, 'utf-8'))
		authMesg = 'AUTH LOGIN\r\n'
		crlfMesg = '\r\n'
		print(authMesg)
		sock.send(authMesg.encode('utf-8'))
		respon = sock.recv(2048)
		print(str(respon, 'utf-8'))
		user64 = base64.b64encode(username.encode('utf-8'))
		pass64 = base64.b64encode(password.encode('utf-8'))
		print(user64)
		sock.send(user64)
		sock.send(crlfMesg.encode('utf-8'))
		respon = sock.recv(2048)
		print(str(respon, 'utf-8'))
		print(pass64)
		sock.send(pass64)
		sock.send(crlfMesg.encode('utf-8'))
		respon = sock.recv(2048)
		print(str(respon, 'utf-8'))
		fromMesg = 'MAIL FROM: <' + mailfrom + '>\r\n'
		print(fromMesg)
		sock.send(fromMesg.encode('utf-8'))
		respon = sock.recv(2048)
		print(str(respon, 'utf-8'))
		rcptMesg = 'RCPT TO: <' + mailrcpt + '>\r\n'
		print(rcptMesg)
		sock.send(rcptMesg.encode('utf-8'))
		respon = sock.recv(2048)
		print(str(respon, 'utf-8'))
		dataMesg = 'DATA\r\n'
		print(dataMesg)
		sock.send(dataMesg.encode('utf-8'))
		respon = sock.recv(2048)
		print(str(respon, 'utf-8'))
		mailbody = mailmess + '\r\n'
		print(mailbody)
		sock.send(mailbody.encode('utf-8'))
		fullStop = '\r\n.\r\n'
		print(fullStop)
		sock.send(fullStop.encode('utf-8'))
		respon = sock.recv(2048)
		print(str(respon, 'utf-8'))
		quitMesg = 'QUIT\r\n'
		print(quitMesg)
		sock.send(quitMesg.encode('utf-8'))
		respon = sock.recv(2048)
		print(str(respon, 'utf-8'))
		sock.close()
		if self.log_en==True:
			now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			logging.error(now + ' : ' + 'email send to user')
		


	def accounting(self, fsize):
		if(str(self.conf_dict['accounting']['enable'])!='True'):
			return True
		else:
			for i in range(0,len(self.conf_dict['accounting']['users'])):
				if(username == self.conf_dict['accounting']['users'][i]['user']):
					rest_size = int(self.conf_dict['accounting']['users'][i]['size'])
					if(rest_size >= fsize):
						new_rest_size = int(rest_size)-int(fsize)
						self.conf_dict['accounting']['users'][i]['size']=str(new_rest_size)
						with open(json_name,'w') as conf:
							json.dump(self.conf_dict,conf,indent=5) 
						if new_rest_size < self.conf_dict['accounting']['threshold']:
							email_en = False
							email_en = conf_dict['accounting']['users'][i]['alert']
							index = i
							if email_en == True:
								if self.log_en==True:
									now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
									logging.error(now + ' : ' + 'space is less than threshold')
								self.send_email(index)
						message = '‫‪remaining space: '+str(new_rest_size)+' .‬‬\r\n'
						print(message)
						
						return True
					else:
						return False

	def PWD(self, cmd):
		if not self.check_auth():
			message='‫‪332‬‬ ‫‪Need‬‬ ‫‪account‬‬ ‫‪for‬‬ ‫‪login.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' + message)
			return
		message='257 '+  self.cwd +'.\r\n'
		self.client.sendall(message.encode('utf-8'))
		if self.log_en==True:
			now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			logging.info(now + ' : ' + message)

	def MKD(self, cmd):
		if not self.check_auth():
			message='‫‪332‬‬ ‫‪Need‬‬ ‫‪account‬‬ ‫‪for‬‬ ‫‪login.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' + message)
			return
		path = cmd[4:].strip()
		if path[0:2]!='-i':
			dirname = os.path.join(self.cwd, path)
		try:
			if not path:
				message='501 Missing arguments <dirname>.\r\n'
				self.client.sendall(message.encode('utf-8'))
				if self.log_en==True:
					now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					logging.error(now + ' : ' + message)
			else:
				if path[0:2]!='-i':
					os.mkdir(dirname)
					message='250 Directory created: ' + dirname + '.\r\n'
					self.client.sendall(message.encode('utf-8'))
					if self.log_en==True:
						now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						logging.info(now + ' : ' + message)
				else:
					file_name = path[3:].strip()
					open(file_name , 'w+')
					message='250 File created: ' + file_name + '.\r\n'
					self.client.sendall(message.encode('utf-8'))
					if self.log_en==True:
						now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						logging.info(now + ' : ' + message)
		except Exception as e:
			print ('500 ERROR: ' + str(self.client_address) + ': ' + str(e))
			message='550 Failed to create directory/file ' + dirname + '.'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : 500 ERROR')
				logging.error(now + ' : ' + message)

	def RMD(self, cmd):
		if not self.check_auth():
			message='‫‪332‬‬ ‫‪Need‬‬ ‫‪account‬‬ ‫‪for‬‬ ‫‪login.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' + message)
			return
		path = cmd[4:].strip()
		if path[0:2]=='-f':
			directory = path[3:].strip()
			dirname = os.path.join(self.cwd, directory)
		try:
			if not path:
				message='501 Missing arguments <dirname>.\r\n'
				self.client.sendall(message.encode('utf-8'))
				if self.log_en==True:
					now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					logging.error(now + ' : ' + message)
			else:
				if path[0:2]=='-f':
					os.rmdir(dirname)
					message='250 Directory deleted: ' + dirname + '.\r\n'
					self.client.sendall(message.encode('utf-8'))
					if self.log_en==True:
						now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						logging.info(now + ' : ' + message)
				else:
					file_name = path[0:].strip()
					os.remove(file_name)
					message='250 File deleted: ' + file_name + '.\r\n'
					self.client.sendall(message.encode('utf-8'))
					if self.log_en==True:
						now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						logging.info(now + ' : ' + message)
		except Exception as e:
			print ('500 ERROR: ' + str(self.client_address) + ': ' + str(e))
			message='550 Failed to delete directory ' + dirname + '.'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : 500 ERROR')
				logging.error(now + ' : ' + message)

	def LIST(self, cmd):
		if not self.check_auth():
			message='‫‪332‬‬ ‫‪Need‬‬ ‫‪account‬‬ ‫‪for‬‬ ‫‪login.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' + message)
			return
		print ('LIST', self.cwd)
		client_data,client_address = self.start_datasock()

		try:
			listdir = os.listdir(self.cwd)
			if not len(listdir):
				max_length = 0
			else:
				max_length = len(max(listdir, key=len))

			header = '| %*s | %9s | %12s | %20s | %11s | %12s |' % (max_length, 'Name', 'Filetype', 'Filesize', 'Last Modified', 'Permission', 'User/Group')
			table = '%s\n%s\n%s\n' % ('-' * len(header), header, '-' * len(header))
			client_data.sendall(table.encode('utf-8'))
			
			for i in listdir:
				path = os.path.join(self.cwd, i)
				stat = os.stat(path)
				data = '| %*s | %9s | %12s | %20s | %11s | %12s |\n' % (max_length, i, 'Directory' if os.path.isdir(path) else 'File', str(stat.st_size) + 'B', time.strftime('%b %d, %Y %H:%M', time.localtime(stat.st_mtime))
					, oct(stat.st_mode)[-4:], str(stat.st_uid) + '/' + str(stat.st_gid)) 
				client_data.sendall(data.encode('utf-8'))
			
			table = '%s\n' % ('-' * len(header))
			client_data.sendall(table.encode('utf-8'))
			message='\r\n226 ‫‪List‬‬ ‫‪transfer‬‬ ‫‪done.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.info(now + ' : 226 ‫‪List‬‬ ‫‪transfer‬‬ ‫‪done.‬‬')
		except Exception as e:
			print ('500 ERROR: ' + str(self.client_address) + ': ' + str(e))
			message='426 Connection closed; transfer aborted.\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : 500 ERROR')
				logging.error(now + ' : ' + message)
		finally: 
			client_data.close()
			self.close_datasock()

	def CWD(self, cmd):
		if not self.check_auth():
			message='‫‪332‬‬ ‫‪Need‬‬ ‫‪account‬‬ ‫‪for‬‬ ‫‪login.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' + message)
			return
		if(len(cmd[4:].strip())!=0):
			if(cmd[4:].strip()=='..'):
				dest = os.path.abspath(os.path.join(self.cwd, '..'))
				if(os.path.isdir(dest)):
					self.cwd = dest
					message='250 OK ‫‪Successful‬‬ ‫‪Change to parent directory.‬‬\r\n'
					self.client.sendall(message.encode('utf-8'))
					if self.log_en==True:
						now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						logging.info(now + ' : ' + message)
				else:
					print ('500 ERROR: ' + str(self.client_address) + ': No such file or directory.\n')
					message='550 \"' + dest + '\": No such file or directory.\r\n'
					self.client.sendall(message.encode('utf-8'))
					if self.log_en==True:
						now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						logging.error(now + ' : 500 ERROR')
						logging.error(now + ' : ' + message)
			else:
				dest = os.path.join(self.cwd, cmd[4:].strip())
				if(os.path.isdir(dest)):
					self.cwd = dest
					message='250 OK ‫‪Successful‬‬ ‫‪Change.‬‬\r\n'
					self.client.sendall(message.encode('utf-8'))
					if self.log_en==True:
						now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						logging.info(now + ' : ' + message)
				else:
					print ('500 ERROR: ' + str(self.client_address) + ': No such file or directory.\n')
					message='550 \"' + dest + '\": No such file or directory.\r\n'
					self.client.sendall(message.encode('utf-8'))
					if self.log_en==True:
						now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						logging.error(now + ' : 500 ERROR')
						logging.error(now + ' : ' + message)
		else:
			self.cwd=self.first_cwd
			message='250 OK ‫‪Successful‬‬ ‫‪Change to first directory.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.info(now + ' : ' + message)

	def DL(self, cmd):
		if not self.check_auth():
			message='‫‪332‬‬ ‫‪Need‬‬ ‫‪account‬‬ ‫‪for‬‬ ‫‪login.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' + message)
			return
		path = cmd[3:].strip()
		fsize=os.stat(path).st_size	
		if not path:
			message='501 Missing arguments <filename>.\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' + message)
			return

		if self.accounting(fsize):
			fname = os.path.join(self.cwd, path)
			(client_data, client_address) = self.start_datasock()
			if not os.path.isfile(fname):
				message='550 File not found.\r\n'
				self.client.sendall(message.encode('utf-8'))
				if self.log_en==True:
					now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					logging.error(now + ' : ' + message)
			else:
				try:
					file_read = open(fname, "r")
					data = file_read.read(1024)

					while data:
						client_data.sendall(data.encode('utf-8'))
						data = file_read.read(1024)

					message='226 ‫‪Successful‬‬ ‫‪Download.‬‬\r\n'
					self.client.sendall(message.encode('utf-8'))
					if self.log_en==True:
						now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						logging.info(now + ' : 226 ‫‪Successful‬‬ ‫‪Download:' + fname)
				except Exception as e:
					print ('500 ERROR: ' + str(self.client_address) + ': ' + str(e))
					message='426 Connection closed; transfer aborted.\r\n'
					self.client.sendall(message.encode('utf-8'))
					if self.log_en==True:
						now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						logging.error(now + ' : 500 ERROR')
						logging.error(now + ' : ' + message)
				finally:
					client_data.close()
					self.close_datasock()
					file_read.close()
		else:
			message='‫‪425‬‬ ‫‪Cant‬‬ ‫‪open‬‬ ‫‪data‬‬ ‫‪connection.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : 500 ERROR')
				logging.error(now + ' : ' + message)

	def HELP(self,cmd):
		message = "214\n"
		message += "USER [name], Its argument is used to specify the user's name. It is used for authentication.\r\n"
		message += "PASS [password], Its argument is used to specify the user's password. It is used for authentication.\r\n"
		message += "PWD, It is used to get current working directory\r\n"
		message += "MKD [flag] [name], Its argument is used to specify the file/directory path. Flag: -i, If present, a new file will be created and otherwise a new directory. It is usede for creating a new file or directory.\n"
		message += "RMD [flag] [name], Its argument is used to specify the file/directory path. Flag: -f, If present, a directory will be removed and otherwise a file. It is usede for removing a file or directory.\n"
		message += "LIST, It is used to get information of a directory or file,or information of current working directory if not specified\r\n"
		message += "CWD [path], Its argument is used to specify the directory's path. It is used for changing the current working directory.\r\n"
		message += "DL [name], Its argument is used to specify the file's name. It is used for retrieve file from current working directory\r\n"
		message += "HELP, It is used for printing list of availibale commands.\r\n"
		message += "QUIT, It is used for signing out from the server.\r\n"
		self.client.send(message.encode('utf-8'))

	def QUIT(self, cmd):
		if not self.check_auth():
			message='‫‪332‬‬ ‫‪Need‬‬ ‫‪account‬‬ ‫‪for‬‬ ‫‪login.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : ' + message)
			return
		try:
			message='221‫‪ Successful‬‬ ‫‪Quit.‬‬\r\n'
			self.client.sendall(message.encode('utf-8'))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.info(now + ' : ' + message)
		except:
			pass
		finally:
			print ('Closing connection from ' + str(self.client_address) + '...')
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.error(now + ' : Closing connection')
			self.close_datasock()
			self.client.close()
			quit()



class FTPserver:
	def __init__(self, port, data_port, conf_dict):
		# server address at localhost
		self.address = '127.0.0.1'
		self.port = int(port)
		self.data_port = int(data_port)
		self.conf_dict = conf_dict
		self.log_file=""
		self.log_en=False

	def check_log(self):
		en = self.conf_dict['logging']['enable']
		if en==True:
			self.log_en=True
			self.log_file=self.conf_dict['logging']['path']
			logging.basicConfig(filename=self.log_file,level=logging.NOTSET)
			return True
		else:
			return False

	def start_sock(self):
		# create TCP socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_address = (self.address, self.port)
		self.check_log()

		try:
			print ('Creating data socket on', self.address, ':', self.port, '...')
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.info(now + ' : Creating data socket')
			self.sock.bind(server_address)
			self.sock.listen(5)
			print ('Server is up. Listening to', self.address, ':', self.port)
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.info(now + ' : Server is up. Listening ')
		except Exception as e:
			print ('Failed to create server on', self.address, ':', self.port, 'because', str(e.strerror))
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.info(now + ' : Failed to create server')
			quit()

	def start(self):
		self.start_sock()

		try:
			while True:
				print ('Waiting for a connection')
				if self.log_en==True:
					now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					logging.info(now + ' : Waiting for a connection')
				client,client_address=self.sock.accept()
				thread = FTPThreadServer(client, client_address, self.address, self.data_port,self.conf_dict,self.log_en)
				thread.daemon = True
				thread.start()
		except KeyboardInterrupt:
			print ('Closing socket connection')
			if self.log_en==True:
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logging.info(now + ' : Closing socket connection')
			self.sock.close()
			quit()


# Main
global json_name
json_name='config.json'
with open('config.json', 'r') as conf:
    conf_dict = json.load(conf)
port = conf_dict['commandChannelPort']
data_port = conf_dict['dataChannelPort']

server = FTPserver(port, data_port, conf_dict)
server.start()