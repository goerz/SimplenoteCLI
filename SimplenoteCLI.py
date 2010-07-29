#!/usr/bin/env python
"""
Executes given CMD, where CMD is one of the following, along with
correspondings ARGS:

list [FILENAME]               -  write list of all notes to FILENAME
                                 (or print to stdout if FILENAME not given)
search SEARCHTERM  [FILENAME] -  write list of notes matching SEARCHTERM to
                                 FILENAME (or print to stdout if FILENAME
                                 not given)
read KEY FILENAME             -  store note with KEY in FILENAME
write KEY FILENAME            -  update note with KEY with data from FILENAME
new FILENAME                  -  create new note from FILENAME
delete KEY                    -  delete note with KEY"""

import sys
import os
import codecs
import cPickle as pickle
from optparse import OptionParser
from optparse import IndentedHelpFormatter
from urllib import urlopen
from base64 import b64encode
try:
    import simplejson
    from simplejson.decoder import JSONDecodeError
except ImportError:
    print >> sys.stderr, "Please install the simplejson module from " \
                         "http://code.google.com/p/simplejson/"
    if __name__ == "__main__":
        sys.exit(1)

API_URL = 'https://simple-note.appspot.com/api/'

class SimpleNoteAuthenticator:
    """ Class for handling authentication with Simplenote Account """
    def __init__(self):
        """ Define class fields """
        self.email = ''
        self.token = ''
        self.token_file = ''
    def del_token_file(self):
        """ Remove TOKEN_FILE """
        if os.path.isfile(self.token_file):
            try:
                os.remove(self.token_file)
            except OSError, data:
                print >> sys.stderr, "Could not remove tokenfile: %s" % data[1]
    def init_token(self, email, password):
        """ Set and return an authentification token """
        login_url = API_URL + 'login'
        creds = b64encode('email=%s&password=%s' % (email, password))
        login = urlopen(login_url, creds)
        self.token = login.readline().rstrip()
        if self.token == '':
            print >> sys.stderr, "Could not get token"
        self.email = email
        login.close()

AUTH = SimpleNoteAuthenticator()


def get_title_line(key, ascii=True):
    """ Get a line of length 80, consisting of the title of the note
        Do not handle IOError exceptions
    """
    note_url = API_URL + "note?key=%s&auth=%s&email=%s" \
               % (key, AUTH.token, AUTH.email)
    note_bytes = urlopen(note_url)
    title = note_bytes.readline().decode('utf-8').rstrip()
    if len(title) >= 76:
        title = title[:76] + "..."
    else:
        if len(title) <= 60: # add body text until title is 80 cols
            title = title + " |"
            while len(title) <= 80:
                line = note_bytes.readline().decode('utf-8')
                if line == '':
                    break
                line = line.strip()
                if line != '':
                    title = title + " " + line.strip()
            if  len(title) > 80:
                title = title[:80]
            if len(title) < 80:
                title = title + " "*(80-len(title))
    if ascii:
        title = title.encode('ascii', 'ignore')
        if len(title) < 80:
            title = title + " "*(80-len(title))
    return title


def get_note_list():
    """Get data-structure containing index of all notes """
    index_url = API_URL + 'index?auth=%s&email=%s' % (AUTH.token, AUTH.email)
    try:
        index = urlopen(index_url)
    except IOError, data:
        print >> sys.stderr, \
        "Failed to get list of notes from server:", data[2]
        return None
    try:
        return simplejson.load(index)
    except JSONDecodeError:
        print >> sys.stderr, "Failed to decode index"
        return None


def list_notes(outfile=None, cachefile=None):
    """ print a list of all notes, ordered by recent change """

    note_data = {}
    keys_on_server = []
    last_run_date = ""
    most_recent_note_date = ""
    if cachefile is not None and cachefile.startswith('~'):
        cachefile = cachefile.replace('~', os.environ['HOME'], 1)
    if cachefile is not None and os.path.isfile(str(cachefile)):
        picklefh = open(cachefile, 'r')
        note_data = pickle.load(picklefh)
        picklefh.close()
        last_run_date = note_data['last_run_date']
        del note_data['last_run_date']

    if (outfile is None):
        ascii = True
        out = sys.stdout
    else:
        ascii = False
        out = codecs.open(outfile, "w", "utf-8")

    for note in get_note_list():
        if note['deleted'] is False:
            key = note['key']
            keys_on_server.append(key)
            if note['modify'] > most_recent_note_date:
                most_recent_note_date = note['modify']
            if ( note['modify'] >= last_run_date
            or key not in note_data.keys() ):
                try:
                    note_data[key] = {
                    'modify':note['modify'],
                    'title': get_title_line(key, ascii)}
                except IOError, data:
                    print >> sys.stderr, \
                    "Failed to get note title for key %s : %s" % (data[2], key)
                    continue
    keys_list = note_data.keys()
    keys_list.sort(key=lambda k: note_data[k]['modify'], reverse=True)

    for key in keys_list:
        if key not in keys_on_server:
            del note_data[key]
            continue
        print >> out, "%s (%s)" % (note_data[key]['title'], key)

    if cachefile is not None:
        note_data['last_run_date'] = most_recent_note_date
        picklefh = open(cachefile, 'w')
        pickle.dump(note_data, picklefh)
        picklefh.close()

    if (outfile is not None):
        out.close()

    return 0


def search_notes(searchterm, results=10, outfile=None, ascii=True):
    """ Search in Notes """

    index_url = API_URL + 'search?query=%s&results=%s&auth=%s&email=%s' \
                           % (searchterm, results, AUTH.token, AUTH.email)
    try:
        index = urlopen(index_url)
    except IOError, data:
        print >> sys.stderr, \
        "Failed to search in notes on server:", data[2]
        return 1

    if (outfile is None):
        ascii = True
        out = sys.stdout
    else:
        ascii = False
        out = codecs.open(outfile, "w", "utf-8")

    try:
        json_note_list = simplejson.load(index)
    except JSONDecodeError:
        print >> sys.stderr, \
        "Failed to decode search response. Malformed searchterm?"
        return 1

    for note in json_note_list['Response']['Results']:
        note_content = note['content'].replace("\n", " | ", 1)
        title = note_content.replace("\n", "")[:80]
        if ascii:
            title = title.encode('ascii', 'ignore')
        if len(title) < 80:
            title = title + " "*(80-len(title))
        print >> out, "%s (%s)" % (title, note['key'])

    if (outfile is not None):
        out.close()

    return 0


def read_note(key, filename):
    """ Read note with given key from the server and store it in filename """
    note_url = API_URL + "note?key=%s&auth=%s&email=%s" \
               % (key, AUTH.token, AUTH.email)
    outfile = codecs.open(filename, "w", "utf-8")
    result = 0
    try:
        outfile.write(urlopen(note_url).read().decode('utf-8'))
        # TODO: call to 'read' my not read entire stream
    except IOError, data:
        print >> sys.stderr, \
        "Failed to get note text for key %s : %s" % (data[2], key)
        result = 1
    outfile.close()
    return result


def write_note(key, filename):
    """ Update note with given key with text stored in filename """
    note_url = API_URL + "note?key=%s&auth=%s&email=%s" \
               % (key, AUTH.token, AUTH.email)
    infile = codecs.open(filename, "r", "utf-8")
    result = 0
    try:
        result = urlopen( note_url,
                            b64encode(infile.read().decode("utf-8")) ).read()
    except IOError, data:
        print >> sys.stderr, \
        "Failed to set note text for key %s : %s" % (data[2], key)
    infile.close()
    return result


def create_note(filename):
    """ Create a new note from text stored in filename  Return key."""
    note_url = API_URL + "note?auth=%s&email=%s" % (AUTH.token, AUTH.email)
    infile = codecs.open(filename, "r", "utf-8")
    result = ""
    try:
        result = urlopen( note_url,
                          b64encode(infile.read().decode("utf-8")) ).read()
    except IOError, data:
        print >> sys.stderr, \
        "Failed to create note text for key %s : %s" % (data[2])
        result = ""
    infile.close()
    return result


def setup_arg_parser():
    """ Return an arg_parser, set up with all options """
    class MyIndentedHelpFormatter(IndentedHelpFormatter):
        """ Slightly modified formatter for help output: allow paragraphs """
        def format_paragraphs(self, text):
            """ wrap text per paragraph """
            result = ""
            for paragraph in text.split("\n"):
                result += self._format_text(paragraph) + "\n"
            return result
        def format_description(self, description):
            """ format description, honoring paragraphs """
            if description:
                return self.format_paragraphs(description) + "\n"
            else:
                return ""
        def format_epilog(self, epilog):
            """ format epilog, honoring paragraphs """
            if epilog:
                return "\n" + self.format_paragraphs(epilog) + "\n"
            else:
                return ""
    arg_parser = OptionParser(
        formatter=MyIndentedHelpFormatter(),
        usage = "%prog [options] CMD [ARGS] ",
        description = __doc__)
    arg_parser.add_option(
        '--email', action='store', dest='email',
        help="Email address to use for authentification")
    arg_parser.add_option(
        '--password', action='store', dest='password',
        help="Password to use for authentification (Read warning below).")
    arg_parser.add_option(
        '--credfile', action='store', dest='credfile',
        default=os.path.join(os.environ['HOME'], '.simplenotesyncrc'),
        help="File from which to read email (first line) and "
             "password (second line). Defaults to ~/.simplenotesyncrc")
    arg_parser.add_option(
        '--cachefile', action='store', dest='cachefile',
        help="File in which to cache information about notes. "
             "Using a cachefile can dramatically speed up listing notes.")
    arg_parser.add_option(
        '--results', action='store', dest='results', type="int", default=10,
        help="Maximum number of results to be returned in a search")
    arg_parser.epilog = "You are strongly advised to use the --credfile " \
                        "option instead of the --password option. Giving " \
                        "a password in cleartext on the command line will " \
                        "result in that password being visible in the "\
                        "process list and your history file."
    return arg_parser


def cmd_list(options, args):
    """ Execute 'list' command """
    if len(args) > 2:
        return list_notes(outfile=args[2], cachefile=options.cachefile)
    else:
        return list_notes(cachefile=options.cachefile)


def cmd_read(options, args):
    """ Execute 'read' command """
    try:
        key = args[2]
        filename = args[3]
        return read_note(key, filename)
    except IndexError:
        print >> sys.stderr, "read command needs KEY and FILENAME"
        return 2


def cmd_write(options, args):
    """ Execute 'write' command """
    try:
        key = args[2]
        filename = args[3]
        return write_note(key, filename)
    except IndexError:
        print >> sys.stderr, "write command needs KEY and FILENAME"
        return 2


def cmd_search(options, args):
    """ Execute 'search' command """
    try:
        searchterm = args[2]
        if len(args) > 3:
            return search_notes(searchterm, options.results,
                                outfile=args[3], ascii=False)
        else:
            return search_notes(searchterm, options.results,
                                outfile=None, ascii=True)
    except IndexError:
        print >> sys.stderr, "write command needs KEY and FILENAME"
        return 2


def cmd_new(options, args):
    """ Execute 'new' command """
    try:
        filename = args[2]
        key = create_note(filename)
        if isinstance(key, basestring) and len(key) == 38:
            print key
            return 0
        else:
            print >> sys.stdout, "Result: %s" % key
            return 1
    except IndexError:
        print >> sys.stderr, "read command needs KEY and FILENAME"
        return 2


def main(argv=None):
    """ Main program: Select and run command"""
    if argv is None:
        argv = sys.argv
    arg_parser = setup_arg_parser()
    options, args = arg_parser.parse_args(argv)
    if os.path.isfile(options.credfile):
        credfile = open(options.credfile)
        if options.email is None:
            email = credfile.readline().strip()
            options.email = email
        if options.password is None:
            password = credfile.readline().strip()
            options.password = password
        credfile.close()
    AUTH.init_token(options.email, options.password)
    try:
        command = args[1].lower()
    except IndexError:
        arg_parser.error("You have to specify a command. "
                         "Try '--help' for more information")
    cmd_table = { 'list': cmd_list, 'read': cmd_read, 'write': cmd_write,
                  'search': cmd_search, 'new': cmd_new }
    try:
        return cmd_table[command](options, args)
    except IndexError:
        arg_parser.error("Unknown command: %s.\n" % command +
                         "Try '--help' for more information")


if __name__ == "__main__":
    sys.exit(main())
