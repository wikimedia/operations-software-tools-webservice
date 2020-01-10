import errno
import os
import pwd

import yaml

with open("/etc/wmcs-project", "r") as _projectfile:
    PROJECT = _projectfile.read().strip()


class Tool(object):
    PREFIX = PROJECT + "."
    MANIFEST_VERSION = 3

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

    @property
    def manifest(self):
        """
        Return a dict with data from service manifest for current tool
        instance.

        If no service.manifest file is found, returns an empty dict
        """
        if not hasattr(self, "_manifest"):
            try:
                with open(self.get_homedir_subpath("service.manifest")) as f:
                    self._manifest = yaml.safe_load(f)
                if self._manifest is None:
                    self._manifest = {}
            except IOError as e:
                if e.errno == errno.ENOENT:
                    self._manifest = {}
                else:
                    raise
        return self._manifest

    def save_manifest(self):
        """
        Saves modified manifest file to service.manifest

        Never write to service.manifest without an action directly initiated
        by a user (like running a commanad on the commandline). If a race
        happens, whoever wins the os.rename race wins.
        """
        tilde_file_path = self.get_homedir_subpath("service.manifest~")
        tilde_file_fd = os.open(
            tilde_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644
        )
        tilde_file = os.fdopen(tilde_file_fd, "w")
        # Set version if there is none!
        if "version" not in self.manifest:
            self.manifest["version"] = Tool.MANIFEST_VERSION
        try:
            tilde_file.write(
                "# This file is used by toollabs infrastructure.\n"
                "# Please do not edit manually at this time.\n"
            )
            yaml.safe_dump(
                self._manifest, tilde_file, default_flow_style=False
            )
        finally:
            tilde_file.close()

        # We leave behind tilda_file_path if this rename fails for some
        # reason, and then manual intervention is needed, but that seems
        # appropriate
        os.rename(
            tilde_file_path, self.get_homedir_subpath("service.manifest")
        )

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
            raise Tool.InvalidToolException("No tool with name %s" % (name,))
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
            raise Tool.InvalidToolException(
                "Tool username should begin with " + Tool.PREFIX
            )
        if pwd_entry.pw_uid < 50000:  # FIXME: Find if it should be < or <=
            raise Tool.InvalidToolException(
                "uid of tools should be >= 50000, uid is %s" % pwd_entry.pw_uid
            )
        toolname = pwd_entry.pw_name[len(Tool.PREFIX) :]
        return cls(
            toolname,
            pwd_entry.pw_name,
            pwd_entry.pw_uid,
            pwd_entry.pw_gid,
            pwd_entry.pw_dir,
        )
