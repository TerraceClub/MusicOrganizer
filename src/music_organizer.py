#!/usr/bin/python

import os
import sys
import string
import unicodedata
import codecs

from os.path import isdir, splitext, isfile, join, exists, abspath
from mutagen.easyid3 import EasyID3
from mutagen.asf import ASF
from mutagen.oggvorbis import OggVorbis

from mutagen.id3 import ID3NoHeaderError

class InvalidFormatException(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

import unicodedata as ud
all_unicode = ''.join(unichr(i) for i in xrange(65536))
unicode_letters_and_digits = ''.join(c for c in all_unicode if ud.category(c)=='Lu' or ud.category(c)=='Ll' or ud.category(c)=='Nd')

validFilenameChars = "-_.(),&'[] %s" % (unicode_letters_and_digits)

def periodreplace(e):
	if isinstance(e, UnicodeEncodeError):
		result = u''
		for c in e.object:
			result += u'_'
		return (result, e.end)
	else:
		raise e

def slugify(filename):
	cleanedFilename = unicodedata.normalize('NFKD', filename).encode('utf_8', 'periodreplace')
	result = ''
	for c in filename:
		if c in validFilenameChars:
			result += c
		else:
			result += '_'
	return result

def lowerify(s):
	return ''.join([c for c in s.lower() if c.islower()])

def is_duplicate(title, path):
	title = lowerify(title)
	songs = [lowerify(song) for song in os.listdir(path) if isfile(join(path,song))]
	print songs
	for song in songs:
		if title in song:
			return True
	return False

class Organizer:
	def __init__(self, store_dir):
		self.duplicate_count = 0
		self.missingtag_count = 0
		self.invalidformat_count = 0
		self.store_dir = abspath(store_dir)

	def organize(self, directory):
		if not directory:
			return

		filenames = os.listdir(directory)
		for filename in filenames:
			if isdir(filename):
				self.organize(join(directory, filename))
				if os.listdir(filename) == []:
					os.rmdir(join(directory, filename))
			else:
				try:
					artist = ""
					album = "Various Albums"
					title = ""

					basename, extension = splitext(filename)
					extension = extension.lower()

					if extension == ".wma":
						audio = ASF(join(directory, filename))
						title = slugify(unicode(audio["Title"][0]))
						artist = slugify(unicode(audio["Author"][0]))
						try:
							album = slugify(unicode(audio["WM/AlbumTitle"][0]))
						except KeyError:
							pass

					elif extension == ".mp3": 
						audio = EasyID3(join(directory, filename))
						title = slugify(audio["title"][0])
						artist = slugify(audio["artist"][0])
						try:
							album = slugify(audio["album"][0])
						except KeyError:
							pass

					elif extension == ".ogg":
						audio = OggVorbis(join(directory, filename))
						title = slugify(audio["title"][0])
						artist = slugify(audio["artist"][0])
						try:
							album = slugify(audio["album"][0])
						except KeyError:
							pass

					else:
						raise InvalidFormatException(filename)

					mp3directory = join(self.store_dir, artist, album)
					mp3path = join(mp3directory, artist + " - " + title + extension)

					if not exists(mp3directory):
						os.makedirs(mp3directory)
					elif is_duplicate(title, mp3directory):
						self.duplicate_count += 1
						if '-v' in sys.argv:
							print 'Duplicate: ' + join(directory, filename)
					else:
						os.rename(join(directory, filename), mp3path)
				except (ID3NoHeaderError, KeyError):
					self.missingtag_count += 1
					if '-v' in sys.argv:
						print 'Missing tag: ' + join(directory, filename)
				except InvalidFormatException:
					self.invalidformat_count +=1
					if '-v' in sys.argv:
						print 'Invalid format: ' + join(directory, filename)

def main():
	codecs.register_error('periodreplace', periodreplace)
	organizer = Organizer(sys.argv[1])
	organizer.organize(sys.argv[2])

if __name__ == "__main__":
	main()

