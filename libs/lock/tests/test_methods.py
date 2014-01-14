import time
import unittest

from .redis_base import RedisTest
from libs import lock
from libs.lock import exceptions


class LockDataTest(RedisTest):
    def test_request_sets_owner_data(self):
        lock_name = 'foo'
        data = {
            'bar': 'baz'
        }

        result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1, data=data)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.request_id)
        self.assertEqual(result.request_id, result.owner_id)
        self.assertEqual(result.owner_data, data)

    def test_request_returns_owner_data(self):
        lock_name = 'foo'
        data = {
            'bar': 'baz'
        }

        result = lock.request_lock(
                self.connection, lock_name, timeout_seconds=1, data=data)
        self.assertTrue(result.success)

        new_result = lock.request_lock(
                self.connection, lock_name, timeout_seconds=1)
        self.assertFalse(new_result.success)
        self.assertEqual(result.request_id, new_result.owner_id)
        self.assertEqual(data, new_result.owner_data)


class ExclusiveLockNoLockNameTest(RedisTest):
    def test_request_with_empty_lock_name_fails(self):
        lock_name = ''
        with self.assertRaises(exceptions.NoLockName):
            lock.request_lock(self.connection, lock_name,
                    timeout_seconds=1)

    def test_retry_with_empty_lock_name_fails(self):
        lock_name = ''
        with self.assertRaises(exceptions.NoLockName):
            lock.retry_request(self.connection, lock_name, request_id=1)

    def test_try_lock_with_empty_lock_name_fails(self):
        lock_name = ''
        with self.assertRaises(exceptions.NoLockName):
            lock.try_lock(self.connection, lock_name, timeout_seconds=1)

    def test_heartbeat_with_empty_lock_name_fails(self):
        lock_name = ''
        with self.assertRaises(exceptions.NoLockName):
            lock.heartbeat(self.connection, lock_name, request_id=1)

    def test_release_with_empty_lock_name_fails(self):
        lock_name = ''
        with self.assertRaises(exceptions.NoLockName):
            lock.release_lock(self.connection, lock_name, request_id=1)


class ExclusiveLockNoContentionTest(RedisTest):
    def test_request_released_lock_succeeds(self):
        lock_name = 'foo'

        result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertTrue(result.success)
        lock.release_lock(self.connection, lock_name, result.request_id)

        new_result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertTrue(new_result.success)
        self.assertNotEqual(result.request_id, new_result.request_id)
        lock.release_lock(self.connection, lock_name, new_result.request_id)

    def test_release_invalid_request_id_fails(self):
        lock_name = 'foo'

        result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertTrue(result.success)

        invalid_request_id = 'INVALID_PREFIX_' + result.request_id
        with self.assertRaises(exceptions.RequestIdMismatch):
            lock.release_lock(self.connection, lock_name, invalid_request_id)

    def test_release_expired_lock_fails(self):
        lock_name = 'foo'

        result = lock.request_lock(self.connection, lock_name,
                timeout_milliseconds=10)
        self.assertTrue(result.success)

        time.sleep(0.020)

        with self.assertRaises(exceptions.NonExistantLock):
            lock.release_lock(self.connection, lock_name, result.request_id)

    def test_heartbeat_extends_ttl(self):
        lock_name = 'foo'

        result = lock.request_lock(self.connection, lock_name,
                timeout_milliseconds=30)
        self.assertTrue(result.success)
        time.sleep(0.020)

        lock.heartbeat(self.connection, lock_name, result.request_id)
        time.sleep(0.020)
        lock.release_lock(self.connection, lock_name, result.request_id)

    def test_request_expired_lock_succeeds(self):
        lock_name = 'foo'

        result = lock.request_lock(self.connection, lock_name,
                timeout_milliseconds=10)
        self.assertTrue(result.success)

        time.sleep(0.020)
        new_result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertTrue(new_result.success)
        self.assertNotEqual(result.request_id, new_result.request_id)

    def test_heartbeat_valid_lock_succeeds(self):
        lock_name = 'foo'

        result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertTrue(result.success)
        lock.heartbeat(self.connection, lock_name, result.request_id)

    def test_heartbeat_invalid_request_id_fails(self):
        lock_name = 'foo'

        result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertTrue(result.success)

        invalid_request_id = 'INVALID_PREFIX_' + result.request_id
        with self.assertRaises(exceptions.RequestIdMismatch):
            lock.heartbeat(self.connection, lock_name, invalid_request_id)

    def test_heartbeat_expired_lock_fails(self):
        lock_name = 'foo'

        result = lock.request_lock(self.connection, lock_name,
                timeout_milliseconds=10)
        self.assertTrue(result.success)
        time.sleep(0.020)
        with self.assertRaises(exceptions.NonExistantLock):
            lock.heartbeat(self.connection, lock_name, result.request_id)

    def test_request_two_locks_succeeds(self):
        lock_name_a = 'foo'
        lock_name_b = 'bar'

        result_a = lock.request_lock(self.connection, lock_name_a,
                timeout_seconds=1)
        self.assertTrue(result_a.success)

        result_b = lock.request_lock(self.connection, lock_name_b,
                timeout_seconds=1)
        self.assertTrue(result_b.success)

        lock.release_lock(self.connection, lock_name_a, result_a.request_id)
        lock.release_lock(self.connection, lock_name_b, result_b.request_id)


class ExclusiveLockContentionTest(RedisTest):
    def test_retry_existing_lock_fails(self):
        lock_name = 'foo'
        result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertTrue(result.success)

        new_result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertFalse(new_result.success)

        retry_result = lock.retry_request(self.connection,
                lock_name, new_result.request_id)
        self.assertFalse(retry_result.success)
        self.assertEqual(retry_result.owner_id, result.request_id)

    def test_retry_expired_lock_succeeds(self):
        lock_name = 'foo'
        result = lock.request_lock(self.connection, lock_name,
                timeout_milliseconds=10)
        self.assertTrue(result.success)

        new_result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertFalse(new_result.success)

        time.sleep(0.015)

        retry_result = lock.retry_request(self.connection,
                lock_name, new_result.request_id)
        self.assertTrue(retry_result.success)
        self.assertEqual(new_result.request_id, retry_result.owner_id)

    def test_retry_released_lock_succeeds(self):
        lock_name = 'foo'
        result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertTrue(result.success)

        new_result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertFalse(new_result.success)

        lock.release_lock(self.connection, lock_name, result.request_id)

        retry_result = lock.retry_request(self.connection,
                lock_name, new_result.request_id)
        self.assertTrue(retry_result.success)

    def test_retry_invalid_request_id_fails(self):
        lock_name = 'foo'
        result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertTrue(result.success)

        new_result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertFalse(new_result.success)

        invalid_request_id = 'INVALID_PREFIX_' + new_result.request_id
        with self.assertRaises(exceptions.RequestIdMismatch):
            res = lock.retry_request(self.connection, lock_name,
                    invalid_request_id)

    def test_priority_maintained_when_lock_released(self):
        lock_name = 'foo'
        first_result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)

        second_result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertFalse(second_result.success)

        lock.release_lock(self.connection, lock_name, first_result.request_id)
        third_result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertFalse(third_result.success)

    def test_queue_expires(self):
        lock_name = 'foo'
        first_result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        expiring_result = lock.request_lock(self.connection, lock_name,
                timeout_milliseconds=10)

        time.sleep(0.020)

        lock.release_lock(self.connection, lock_name, first_result.request_id)

        second_result = lock.request_lock(self.connection, lock_name,
                timeout_seconds=1)
        self.assertTrue(second_result.success)


if __name__ == '__main__':
    unittest.main()