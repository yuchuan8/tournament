#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM matches")
    conn.commit()
    conn.close()

def deletePlayers():
    """Remove all the player records from the database."""
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM players")
    conn.commit()
    conn.close()

def countPlayers():
    """Returns the number of players currently registered."""
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM players")
    count = c.fetchone()[0]
    return count

def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO players (name) VALUES (%s)", (name,))
    conn.commit()
    conn.close()

def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    conn = connect()
    c = conn.cursor()
    # Count number of wins for each player
    c.execute('''
        CREATE VIEW wins_view AS
        SELECT winner as uid, count(*) as wins
        FROM matches
        GROUP BY winner
        '''
        )
    # Count number of loses for each player
    c.execute('''
        CREATE VIEW loses_view AS
        SELECT loser as uid, count(*) as loses
        FROM matches
        GROUP BY loser
        ''')
    c.execute('''
        SELECT players.id, players.name,
            coalesce(wins_view.wins, 0) as wins,
            coalesce(wins_view.wins, 0) + coalesce(loses_view.loses, 0) as loses
        FROM players
        LEFT JOIN wins_view ON players.id = wins_view.uid
        LEFT JOIN loses_view ON players.id = loses_view.uid
        ORDER BY wins DESC
        '''
        )
    standings = [(row[0], row[1], row[2], row[3]) for row in c.fetchall()]
    conn.close()
    return standings

def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO matches (winner, loser) VALUES (%s, %s)", (winner, loser))
    conn.commit()
    conn.close()

def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """

    # standings are sorted by wins. So just pair each two down the list
    standings = playerStandings()
    pairings = []
    for i in xrange(0, len(standings), 2):
        pairings.append((standings[i][0], standings[i][1], standings[i+1][0], standings[i+1][1]))
    return pairings


