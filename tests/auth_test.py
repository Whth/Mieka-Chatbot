import unittest
from pathlib import Path

from constant import CONFIG_DIR
from modules.auth.permissions import Permission
from modules.auth.resources import Resource, RequiredPermission, required_perm_generator
from modules.auth.roles import Role
from modules.auth.users import User, UserManager


def hello_world():
    print("Hello World")


def this_is_resource(ct: int):
    print(f"the input is {ct}")


def add_one(ct: int) -> int:
    return ct + 1


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.config_file_path = f"../{CONFIG_DIR}/test.json"
        self.permission = Permission(id=1, name="hello")
        self.req = RequiredPermission(id=1, name="srcPerm", execute=[self.permission])
        self.res_1 = Resource(source=hello_world, id=1, name="testRes", required_permissions=self.req)
        self.res_2 = Resource(source=this_is_resource, id=2, name="testResthis", required_permissions=self.req)
        self.res_3 = Resource(source=add_one, id=3, name="testResAddOne", required_permissions=self.req)
        self.user_manager = UserManager(id=1, name="testUserManager", config_file_path=self.config_file_path)
        self.user_manager.load_object_list() if Path("test.json").exists() else None
        self.user = User(id=5, name="testUser")

        self.role = Role(id=1, name="testRole")

        self.role.add_permission(Permission(id=1, name="kreas"))
        self.role.add_permission(self.permission)
        self.user.add_role(self.role)
        self.user_manager.add_object(self.user)

    def test_resource_read(self):
        print("this is resource")
        print(self.res_1.dict())
        print(self.res_1.get_read([]))
        assert id(self.res_1.get_read([])) == id(hello_world)

    def test_user_manager_to_dict(self):
        print("user manager dict")
        print(self.user_manager.dict())

    def test_res_execute(self):
        with self.role as perm:
            print(perm)
            self.res_1.get_execute(perm)
            self.res_2.get_execute(perm, ct=1)
            print(self.res_3.get_execute(perm, ct=1))

    def test_remove_object(self):
        self.user_manager.remove_object(self.user)

    def test_save_object_list(self):
        self.user_manager.save_object_list()


class ToolsTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_req_perm_creator(self):
        extra = Permission(id=16, name="su")
        req = required_perm_generator(target_resource_name="test", extra_permissions=[extra])
        print(req.dict())


if __name__ == "__main__":
    unittest.main()
