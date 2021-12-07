import unittest
from textwrap import dedent

from bot30.models import (
    QuakePlayer,
    QuakePlayers,
)


class QuakePlayerTestCase(unittest.TestCase):

    def test_from_string(self):
        s = '''\
        0:foo^7 TEAM:RED KILLS:20 DEATHS:22 ASSISTS:3 PING:98 AUTH:foo IP:127.0.0.1
        '''
        player = QuakePlayer.from_string(dedent(s))
        self.assertEqual(player.name, 'foo')
        self.assertEqual(player.team, 'RED')
        self.assertEqual(player.kills, 20)
        self.assertEqual(player.deaths, 22)
        self.assertEqual(player.assists, 3)

    def test_order_name(self):
        s1 = '''\
        0:foo^7 TEAM:RED KILLS:20 DEATHS:22 ASSISTS:3 PING:98 AUTH:foo IP:127.0.0.1
        '''
        s2 = '''\
        1:bar^7 TEAM:RED KILLS:20 DEATHS:22 ASSISTS:3 PING:98 AUTH:bar IP:127.0.0.1
        '''
        p1 = QuakePlayer.from_string(dedent(s1))
        p2 = QuakePlayer.from_string(dedent(s2))
        self.assertLess(p2, p1)

    def test_order_kills(self):
        s1 = '''\
        0:foo^7 TEAM:RED KILLS:24 DEATHS:22 ASSISTS:3 PING:98 AUTH:foo IP:127.0.0.1
        '''
        s2 = '''\
        1:bar^7 TEAM:RED KILLS:20 DEATHS:22 ASSISTS:3 PING:98 AUTH:bar IP:127.0.0.1
        '''
        p1 = QuakePlayer.from_string(dedent(s1))
        p2 = QuakePlayer.from_string(dedent(s2))
        self.assertLess(p2, p1)

    def test_order_deaths(self):
        s1 = '''\
        0:foo^7 TEAM:RED KILLS:20 DEATHS:20 ASSISTS:3 PING:98 AUTH:foo IP:127.0.0.1
        '''
        s2 = '''\
        1:bar^7 TEAM:RED KILLS:20 DEATHS:22 ASSISTS:3 PING:98 AUTH:bar IP:127.0.0.1
        '''
        p1 = QuakePlayer.from_string(dedent(s1))
        p2 = QuakePlayer.from_string(dedent(s2))
        self.assertLess(p2, p1)

    def test_order_assists(self):
        s1 = '''\
        0:foo^7 TEAM:RED KILLS:20 DEATHS:22 ASSISTS:5 PING:98 AUTH:foo IP:127.0.0.1
        '''
        s2 = '''\
        1:bar^7 TEAM:RED KILLS:20 DEATHS:22 ASSISTS:3 PING:98 AUTH:bar IP:127.0.0.1
        '''
        p1 = QuakePlayer.from_string(dedent(s1))
        p2 = QuakePlayer.from_string(dedent(s2))
        self.assertLess(p2, p1)


class QuakePlayersTestCase(unittest.TestCase):

    def test_from_string_ctf(self):
        s = '''\
        Map: ut4_abbey
        Players: 3
        GameType: CTF
        Scores: R:5 B:10
        MatchMode: OFF
        WarmupPhase: NO
        GameTime: 00:12:04
        0:foo^7 TEAM:RED KILLS:15 DEATHS:22 ASSISTS:0 PING:98 AUTH:foo IP:127.0.0.1
        1:bar^7 TEAM:BLUE KILLS:20 DEATHS:9 ASSISTS:0 PING:98 AUTH:bar IP:127.0.0.1
        2:baz^7 TEAM:RED KILLS:32 DEATHS:18 ASSISTS:0 PING:98 AUTH:baz IP:127.0.0.1
        '''
        players = QuakePlayers.from_string(dedent(s))
        self.assertEqual(players.mapname, 'ut4_abbey')
        self.assertEqual(players.player_count, 3)
        self.assertEqual(players.gametype, 'CTF')
        self.assertEqual(players.score_red, '5')
        self.assertEqual(players.score_blue, '10')
        self.assertEqual(players.gametime, '00:12:04')
        self.assertEqual(len(players.players), 3)
        self.assertListEqual([p.name for p in players.team_red], ['baz', 'foo'])

    def test_from_string_ffa(self):
        s = '''\
        Map: ut4_docks
        Players: 3
        GameType: FFA
        MatchMode: OFF
        WarmupPhase: NO
        GameTime: 00:12:04
        0:foo^7 TEAM:FREE KILLS:15 DEATHS:22 ASSISTS:0 PING:98 AUTH:foo IP:127.0.0.1
        1:bar^7 TEAM:FREE KILLS:20 DEATHS:9 ASSISTS:0 PING:98 AUTH:bar IP:127.0.0.1
        2:baz^7 TEAM:FREE KILLS:32 DEATHS:18 ASSISTS:0 PING:98 AUTH:baz IP:127.0.0.1
        '''
        players = QuakePlayers.from_string(dedent(s))
        self.assertEqual(players.mapname, 'ut4_docks')
        self.assertEqual(players.player_count, 3)
        self.assertEqual(players.gametype, 'FFA')
        self.assertIsNone(players.score_red)
        self.assertIsNone(players.score_blue)
        self.assertEqual(players.gametime, '00:12:04')
        self.assertEqual(len(players.players), 3)
        self.assertListEqual([p.name for p in players.team_free], ['baz', 'bar', 'foo'])
