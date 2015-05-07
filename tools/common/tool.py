import os
import pwd


class Tool(object):
    PREFIX = 'tools.'

    class InvalidToolException(Exception):
        pass

    def __init__(self, name, username, uid, gid, home):
        self.name = name
        self.uid = uid
        self.gid = gid
        self.username = username
        self.home = home

    def get_homedir_subpath(self, path):
        return os.path.join(self.home, path)

    @classmethod
    def from_name(cls, name):
        """
        Create a Tool instance from a tool name
        """
        username = Tool.PREFIX + name
        try:
            user_info = pwd.getpwnam(username)
        except KeyError:
            # No such user was found
            raise Tool.InvalidToolException("No tool with name %s" % (name, ))
        return Tool.from_pwd(user_info)

    @classmethod
    def from_currentuser(cls):
        """
        Create a Tool instance for the current running user
        """
        pwd_entry = pwd.getpwuid(os.geteuid())
        return Tool.from_pwd(pwd_entry)

    @classmethod
    def from_pwd(cls, pwd_entry):
        """
        Creates a Tool instance from a given pwd entry
        """
        if not pwd_entry.pw_name.startswith(Tool.PREFIX):
            raise Tool.InvalidToolException('Tool username should begin with tools.')
        if pwd_entry.pw_uid < 50000:  # FIXME: Find if it should be < or <=
            raise Tool.InvalidToolException("uid of tools should be >= 50000, uid is %s" % pwd_entry.pw_uid)
        toolname = pwd_entry.pw_name[len(Tool.PREFIX):]
        return cls(toolname, pwd_entry.pw_name, pwd_entry.pw_uid, pwd_entry.pw_gid, pwd_entry.pw_dir)
