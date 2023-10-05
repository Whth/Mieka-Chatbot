import unittest

from constant import CONFIG_DIR
from modules.auth.core import AuthorizationManager
from modules.auth.permissions import Permission
from modules.auth.resources import Resource, RequiredPermission, required_perm_generator, ResourceManager
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

        self.user = User(id=5, name="testUser")

        self.role = Role(id=1, name="testRole")

        self.role.add_permission(Permission(id=1, name="kreas"))
        self.role.add_permission(self.permission)
        self.user.add_role(self.role)
        self.user_manager.add_object(self.user)

    def test_role_perm(self):
        perm = Permission(id=4, name="test")
        perm_2 = Permission(id=4, name="test")
        print(id(perm), id(perm_2))
        role = Role(id=1, name="test", permissions=[perm])
        new_role = Role(**role.dict())
        print(new_role.dict())

    def test_resource_read(self):
        print("this is resource")
        print(self.res_1.dict())
        with self.assertRaises(PermissionError):
            # should raise PermissionError, since read is not allowed for callable
            self.res_1.get_read([])

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

    def test_delete_object(self):
        self.res_1.get_execute([self.permission])  # should work
        self.res_1.get_delete([])
        with self.assertRaises(PermissionError):
            # not allowed to delete a resource twice
            self.res_1.get_delete([])
        with self.assertRaises(TypeError):
            # invalid call, since the source is already deleted
            self.res_1.get_execute([self.permission])


class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.su = Permission(id=32, name="su")

    def test_req_perm_creator(self):
        with self.assertRaises(KeyError):
            # should raise KeyError, since the id is illegal
            Permission(id=52, name="su")

        req = required_perm_generator(target_resource_name="test", super_permissions=[self.su])
        print(req.dict())

    def test_resource_creator(self):
        new_src = [12, 35]
        src = Resource(
            source=hello_world,
            id=1,
            name="testRes",
            required_permissions=required_perm_generator(target_resource_name="testRes", super_permissions=[self.su]),
        )
        with self.assertRaises(PermissionError):
            # should raise PermissionError, since the insufficient permissions
            src.get_read([])
        with self.assertRaises(PermissionError):
            # should raise PermissionError, since the callable resource cannot be read
            src.get_read([self.su])
        src.get_execute([self.su])  # should work
        src.update_source([self.su], new_src)  # should work
        print(src.get_read([self.su]))


class ResourceManagerTest(unittest.TestCase):
    def setUp(self):
        self.manager = ResourceManager(id=1, name="resourceManager", config_file_path=f"../{CONFIG_DIR}/test.json")

    def test(self):
        p = Resource(
            source=hello_world,
            id=1,
            name="testRes",
            required_permissions=required_perm_generator(target_resource_name="testRes"),
        )
        self.manager.add_object(p)
        print(self.manager.dict())
        self.manager.save_object_list()


class AuthCoreTest(unittest.TestCase):
    def setUp(self):
        self.manager = AuthorizationManager(id=1, name="authManager", config_file_path=f"../{CONFIG_DIR}/auth.json")
        self.resource_list = [[12, 35], {14: 16, 17: 18}, lambda x: x + 1]
        self.perms = [Permission(id=1, name="hall"), Permission(id=2, name="hall"), Permission(id=4, name="hall")]

    def test_add_resource(self):
        self.manager.add_resource(resource_id=3, resource_name="testRes", source=self.resource_list[0])
        self.manager.add_resource(resource_id=1, resource_name="testRes", source=self.resource_list[1])
        self.manager.add_resource(resource_id=2, resource_name="testRes", source=self.resource_list[2])
        print(self.manager.dict())

    def test_add_perm(self):
        self.manager.add_perm(self.perms[0].id, self.perms[0].name)
        self.manager.add_perm(self.perms[1].id, self.perms[1].name)
        self.manager.add_perm(self.perms[2].id, self.perms[2].name)
        print(self.manager.dict())

    def test_add_role(self):
        self.manager.add_perm(self.perms[0].id, self.perms[0].name)
        self.manager.add_perm(self.perms[1].id, self.perms[1].name)
        self.manager.add_perm(self.perms[2].id, self.perms[2].name)
        print(self.manager.add_role(role_id=1, role_name="hall", role_perms=[self.perms[0].unique_label]))
        print(self.manager.add_role(role_id=2, role_name="hall", role_perms=[self.perms[1].unique_label]))
        print(self.manager.add_role(role_id=4, role_name="hall", role_perms=[self.perms[2].unique_label]))
        print(self.manager.dict())


if __name__ == "__main__":
    unittest.main()
