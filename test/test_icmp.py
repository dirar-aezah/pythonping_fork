import unittest
from pythonping import icmp


class ICMPTestCase(unittest.TestCase):
    """Tests for the ICMP class"""

    def test_checksum(self):
        """Verifies that checksum calculation is correct"""
        self.assertEqual(
            icmp.checksum(b'\x08\x00\x00\x00\x00*\x01\x009TPM'),
            13421,
            "Checksum validation failed"
        )
        self.assertEqual(
            icmp.checksum(b'\x08\x00\x00\x00\x01*\x01\x001PJ2'),
            21370,
            "Checksum validation failed"
        )
        self.assertEqual(
            icmp.checksum(b'\x08\x00\x00\x00\x02*\x01\x006K3J'),
            16523,
            "Checksum validation failed"
        )
        self.assertEqual(
            icmp.checksum(b'\x08\x00\x00\x00\x03*\x01\x00COSA'),
            17757,
            "Checksum validation failed"
        )

    def test_pack(self):
        """Verifies that creates the correct pack"""
        self.assertEqual(
            icmp.ICMP(icmp.Types.EchoReply, payload='banana', identifier=1).packet,
            b'\x00\x00\xbe\xdb\x01\x00\x01\x00banana',
            "Fail to pack ICMP structure to packet"
        )
        self.assertEqual(
            icmp.ICMP(icmp.Types.EchoReply, payload='random text goes here', identifier=16).packet,
            b'\x00\x00Q\x9d\x10\x00\x01\x00random text goes here',
            "Fail to pack ICMP structure to packet"
        )
        self.assertEqual(
            icmp.ICMP(icmp.Types.EchoRequest, payload='random text goes here', identifier=16).packet,
            b'\x08\x00I\x9d\x10\x00\x01\x00random text goes here',
            "Fail to unpack ICMP structure to packet"
        )

    def test_unpack(self):
        """Verifies that reads data correctly from a packet"""
        ip_header_offset = b''.join([b'0' for _ in range(20)])

        packet = icmp.ICMP.generate_from_raw(ip_header_offset + b'\x00\x00\xbe\xdb\x01\x00\x01\x00banana')
        self.assertEqual(packet.message_type, 0, 'Failed to extract message type')
        self.assertEqual(packet.message_code, 0, 'Failed to extract message code')
        self.assertEqual(packet.id, 1, 'Failed to extract id')
        self.assertEqual(packet.payload, b'banana', 'Failed to extract payload')

        packet = icmp.ICMP.generate_from_raw(ip_header_offset + b'\x00\x00Q\x9d\x10\x00\x01\x00random text goes here')
        self.assertEqual(packet.message_type, 0, 'Failed to extract message type')
        self.assertEqual(packet.message_code, 0, 'Failed to extract message code')
        self.assertEqual(packet.id, 16, 'Failed to extract id')
        self.assertEqual(packet.payload, b'random text goes here', 'Failed to extract payload')

        packet = icmp.ICMP.generate_from_raw(ip_header_offset + b'\x08\x00I\x9d\x10\x00\x01\x00random text goes here')
        self.assertEqual(packet.message_type, 8, 'Failed to extract message type')
        self.assertEqual(packet.message_code, 0, 'Failed to extract message code')
        self.assertEqual(packet.id, 16, 'Failed to extract id')
        self.assertEqual(packet.payload, b'random text goes here', 'Failed to extract payload')

    def test_is_valid(self):
        """Verifies that understands if receives a packet with valid or invalid checksum"""
        ip_header_offset = b''.join([b'0' for _ in range(20)])
        # Following two packets have a good checksum
        packet = icmp.ICMP.generate_from_raw(ip_header_offset + b'\x00\x00\xbe\xdb\x01\x00\x01\x00banana')
        self.assertEqual(packet.received_checksum, packet.expected_checksum, 'Checksum validation failed')
        packet = icmp.ICMP.generate_from_raw(ip_header_offset + b'\x00\x00Q\x9d\x10\x00\x01\x00random text goes here')
        self.assertEqual(packet.received_checksum, packet.expected_checksum, 'Checksum validation failed')
        # Packet disrupted, \x11 instead of \x10
        packet = icmp.ICMP.generate_from_raw(ip_header_offset + b'\x08\x00I\x9d\x11\x00\x01\x00random text goes here')
        self.assertNotEqual(packet.received_checksum, packet.expected_checksum, 'Checksum validation failed')

    def test_checksum_creation(self):
        """Verifies it generates the correct checksum, given packet data"""
        packet = icmp.ICMP(icmp.Types.EchoRequest, payload='random text goes here', identifier=16)
        self.assertEqual(packet.expected_checksum, 40265, 'Checksum creation failed')
        packet = icmp.ICMP(icmp.Types.EchoReply, payload='foo', identifier=11)
        self.assertEqual(packet.expected_checksum, 8589, 'Checksum creation failed')

    def test_blank_header_creation(self):
        """Verifies it generates the correct header (no checksum) given packet data"""
        packet = icmp.ICMP(icmp.Types.EchoRequest, payload='random text goes here', identifier=16)
        self.assertEqual(packet._header(), b'\x08\x00\x00\x00\x10\x00\x01\x00',
                         'Blank header creation failed (without checksum)')
        packet = icmp.ICMP(icmp.Types.EchoReply, payload='foo', identifier=11)
        self.assertEqual(packet._header(), b'\x00\x00\x00\x00\x0b\x00\x01\x00',
                         'Blank header creation failed (without checksum)')
