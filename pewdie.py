''' ASSUMPTIONS: '''
#
# 1) Only these 15 countries are on YouTube
# 2) All the channel's subscribers come only from these 15 countries (So, PewDiePie's 80M subscribers are only from these 15 countries.)
# 3) Subscribers for a channel are uniformly distributed across these 15 countries, in proportion of their respective YouTube population, with the following rules:
#       (a) If a channel C belongs to one of these 15 countries, then we assume x % (magic number) of that channel's subscribers originate from that home country. So, this country's count is scaled up and rest country counts are scaled down accordingly, for this channel C.
#       (b) Also, y % of these subscribers originate from (non-home-country) countries that have C's language as one of their spoken languages. This y % is then split in proportion to the respective country's language population.
#       (c) z % come from rest of the countries, again, in proportion.
#
# Therefore if C has 100 subs and x = 20%, y = 50%, z = 30%:
#       (a) 20 subs come from C's home country
#       (b) 50 subs come from C's home language speaking countries, except C's home country (as it's already considered in (a)). These 50 subs are split in proportion.
#          Eg. If two countries P and Q (both with population 100) have 10% and 20% of people speaking C's home language, then the math goes:
#               C_language_population_in_P = 10
#               C_language_population_in_Q = 20
#               C_subs_in_P = 50 * C_language_population_in_P/(C_language_population_in_P + C_language_population_in_Q) = 50 * 10/30 = 16.67
#               C_subs_in_Q = 50 * C_language_population_in_Q/(C_language_population_in_P + C_language_population_in_Q) = 33.34
#               Therefore, 50 is split as 17 subs from P and 33 subs from Q.
#       (c) 30 subs, split in proportion to their populations, come from the remaining countries.

from operator import itemgetter
from scipy.optimize import linprog
import copy
import random

def printChannelVotes(channels):
    for channel_obj in channels:
        print "-----------------------------"
        print channel_obj['name']
        print channel_obj['subs']
        printCountryWiseDistribution(channel_obj['distribution'])
        print "\nFinal million subs: "
        print sum(x['count'] for x in channel_obj['distribution'])
        print "\n"
    print "------------------------------"

def printCountryVotes(countries, channels):
    total_votes = 0
    for c in countries:
        count_c = 0
        for ch in channels:
            count_c += getChannelCountryDict(ch,c['country'])['count']
        total_votes += count_c
        print "_________"
        print str(c['country']) + ": " + str(count_c)
    print "Total votes across all countries: " + str(total_votes)

def changeDictValue(obj, key, val):
    obj[key] = val
    return obj

def printCountryWiseDistribution(countries_array):
    countries_array_sorted = sorted(countries_array, key=lambda k: k['count'], reverse = True)
    for country_obj in countries_array_sorted:
        print country_obj

def getChannelCountryDict(channel_obj, this_country):
    return filter(lambda c: c['country'] == this_country, channel_obj['distribution'])[0]

def votes_distribution_fptp(channels,country_data_to_use):

    denominator_all_subs = sum(c['subs'] for c in channels)

    for channel_obj in channels:
        channel_language = channel_obj['language']
        channels_with_channel_language = filter(lambda c: c['language'] == channel_language, channels)
        channels_with_channel_language_total_subs = sum(c['subs'] for c in channels_with_channel_language)
        for country_obj in country_data_to_use:
            population_with_channel_language = country_obj['useful_count'] * country_obj['useful_languages'][channel_language] / 100
            # EITHER
            #   Uniform split language population
            # this_channels_slice = population_with_channel_language / len(channels_with_channel_language)
            # OR
            #   Split according to subs proportion
            this_channels_slice = population_with_channel_language * (channel_obj['subs']/channels_with_channel_language_total_subs)
            channel_subs_in_country = this_channels_slice

            # channel_obj['distribution'].append({'country': country_obj['country'], 'count': round(channel_subs_in_country,2)})
            channel_country_obj = getChannelCountryDict(channel_obj,country_obj['country'])
            channel_country_obj['count'] = round(channel_subs_in_country,2)

    # BASIC EXCLUSIVE SUBS SPLITS DONE. NOW, BIAS THEM UP
    # Loop over countries first, then channels.


    # printChannelVotes(channels)
    # printCountryVotes(country_data_to_use, channels)
    # printCountryWiseDistribution(country_data_to_use)

def winner_fptp(all_channels,all_countries):
    print "\n------------- INITIATING FPTP VOTING -------------\n"
    results = {}
    for channel_obj in all_channels:
        results[channel_obj['name']] = 0

    for country_obj in all_countries:
        this_country = country_obj['country']
        print "________________________"
        print this_country
        max_votes_in_this_country = 0
        winner = {}
        equal_votes_competitors = []

        total_votes_in_country = 0
        for channel_obj in all_channels:
            this_channel_votes_in_this_country = getChannelCountryDict(channel_obj,this_country)['count']
            # print "    " + str(channel_obj['name']) + ": " + str(this_channel_votes_in_this_country)
            total_votes_in_country += this_channel_votes_in_this_country
            if(this_channel_votes_in_this_country > 0):
                if(this_channel_votes_in_this_country > max_votes_in_this_country):
                    max_votes_in_this_country = this_channel_votes_in_this_country
                    winner = channel_obj
                    equal_votes_competitors = [winner]
                elif(this_channel_votes_in_this_country == max_votes_in_this_country):
                    equal_votes_competitors.append(channel_obj)
        # print "Total population involved in voting: " + str(total_votes_in_country)
        country_obj['voting_population'] = round(total_votes_in_country,2)
        if(len(equal_votes_competitors)):
            winner = random.choice(equal_votes_competitors)
            print "Winner " + str(this_country) + ": " + str(winner['name'])
            results[winner['name']] += 1

    print "\nSeats distribution for " + str(len(all_countries)) + " seats (countries):"
    print sorted(results.items(), key=itemgetter(1), reverse = True)
    print "\n"
    print max(results.iterkeys(), key=lambda x: results[x]) + " forms government!"
    print "\n"

def distribute_ranks_among_channels_in_this_country(current_rank,this_country,other_channels_list,total_votes):
    other_channels_list_len = len(other_channels_list)
    lower_rank = current_rank + 1
    upper_rank = current_rank + other_channels_list_len
    # print "lower_rank: " + str(lower_rank)
    # print "upper_rank: " + str(upper_rank)
    # rank_lower_limit = lower_rank * total_votes
    # rank_upper_limit = upper_rank * total_votes
    #
    # rank_middle_sum = 0
    # for i_rank in xrange(lower_rank+1,upper_rank):
    #     rank_middle_sum += i_rank * total_votes
    # rank_final_sum = rank_lower_limit + rank_middle_sum + rank_upper_limit
    all_ranks = range(lower_rank,upper_rank+1)
    ranks_dict = {}
    for i_rank in all_ranks:
        ranks_dict[i_rank] = total_votes
    # print ranks_dict
    for other_channel in other_channels_list:
        # print "        " + str(other_channel['name'])
        other_channel_country_obj = getChannelCountryDict(other_channel,this_country)
        votes_remaining_for_this_channel = total_votes

        if(other_channels_list.index(other_channel) == (other_channels_list_len-1)):
            for i_rank in xrange(lower_rank,upper_rank+1):
                # print "Remain: " + str(votes_remaining_for_this_channel)
                i_ranks_this_channel_got = round(ranks_dict[i_rank],2)
                other_channel_country_obj['ranks'][i_rank] = round((other_channel_country_obj['ranks'][i_rank] + i_ranks_this_channel_got),2)
                ranks_dict[i_rank] = ranks_dict[i_rank] - i_ranks_this_channel_got
                votes_remaining_for_this_channel = votes_remaining_for_this_channel - i_ranks_this_channel_got
                # print str(other_channel_country_obj['ranks'][i_rank]) + " (" + str(i_ranks_this_channel_got) + ")"
        else:
            F = [-1 for x in xrange(0,other_channels_list_len)]
            # print F
            a = [[1 for x in xrange(0,other_channels_list_len)]]
            b = [total_votes]
            F_bounds = [(0,ranks_dict[rank]) for rank in all_ranks]
            # print a
            # print b
            # print F_bounds
            # print "Running LPP"
            res = linprog(F,A_eq=a,b_eq=b,bounds=F_bounds,method='interior-point')
            # print res

            for ith_rank in xrange(0,len(all_ranks)):
                # print "Remain for " + str(all_ranks[ith_rank]) + ": " + str(votes_remaining_for_this_channel)
                if(all_ranks[ith_rank] == upper_rank):
                    i_ranks_this_channel_got = votes_remaining_for_this_channel
                else:
                    # i_ranks_this_channel_got = round(random.uniform(0,min(votes_remaining_for_this_channel,ranks_dict[i_rank])),2)
                    i_ranks_this_channel_got = round(res.x[ith_rank],2)
                other_channel_country_obj['ranks'][all_ranks[ith_rank]] = round((other_channel_country_obj['ranks'][all_ranks[ith_rank]] + i_ranks_this_channel_got),2)
                ranks_dict[all_ranks[ith_rank]] = ranks_dict[all_ranks[ith_rank]] - i_ranks_this_channel_got
                votes_remaining_for_this_channel = votes_remaining_for_this_channel - i_ranks_this_channel_got
                # print str(other_channel_country_obj['ranks'][all_ranks[ith_rank]]) + " (" + str(i_ranks_this_channel_got) + ")"

def votes_distribution_ranked_voting(channels,country_data_to_use):
    # Using votes_distribution_fptp data.
    for country_obj in country_data_to_use:
        this_country = country_obj['country']
        # print "_ _ _ _ _ _"
        # print this_country

        for channel_obj in channels:
            this_channel_votes_in_this_country = getChannelCountryDict(channel_obj,this_country)['count']
            # print "    " + str(channel_obj['name']) + ": " + str(this_channel_votes_in_this_country)
            this_channel_country_obj = getChannelCountryDict(channel_obj,this_country)
            this_channel_country_obj['ranks'][1] += this_channel_votes_in_this_country
            # print "\n" +     str(channel_obj['name']) + " total 1 ranks: " + str(this_channel_country_obj['ranks'][1])

            # print "   For language " + str(channel_obj['language'])
            current_rank = 1
            other_channels_with_channel_language = filter(lambda c: c['language'] == channel_obj['language'] and c['name'] != channel_obj['name'], channels)
            distribute_ranks_among_channels_in_this_country(current_rank,this_country,other_channels_with_channel_language,this_channel_votes_in_this_country)
            #
            # # print "   Remaining channels "
            current_rank += len(other_channels_with_channel_language)
            remaining_channels = filter(lambda c: c['language'] != channel_obj['language'], channels)
            distribute_ranks_among_channels_in_this_country(current_rank,this_country,remaining_channels,this_channel_votes_in_this_country)

    # printChannelVotes(channels)
    # printCountryVotes(country_data_to_use, channels)
    # printCountryWiseDistribution(country_data_to_use)

def distributeEliminatedChannelsVotes(votes_to_distribute,channels_to_distribute_in,this_country):
    while(channels_to_distribute_in): # votes_to_distribute > 0):
        # print "\n   To distribute: " + str(votes_to_distribute)
        random_channel_select = random.choice(channels_to_distribute_in)
        random_channel_select_in_country = getChannelCountryDict(random_channel_select,this_country)
        main_other_ranks = filter(lambda r: r != 1, random_channel_select_in_country['ranks'].keys())
        if(len(channels_to_distribute_in) == 1):
            votes_to_add_to_1_rank = votes_to_distribute
        else:
            votes_to_add_to_1_rank = round(random.uniform(0,votes_to_distribute),2)
        # print  "      Votes added to 1 rank of " + str(random_channel_select['name']) + ": " + str(votes_to_add_to_1_rank)
        random_channel_select_in_country['ranks'][1] = round((random_channel_select_in_country['ranks'][1] + votes_to_add_to_1_rank),2)
        votes_to_subtract_from_other_ranks = votes_to_add_to_1_rank
        while(votes_to_subtract_from_other_ranks > 0):
            other_ranks = copy.copy(main_other_ranks)
            while(other_ranks): # votes_to_subtract_from_other_ranks > 0):
                # print "        votes to subtract from all: " + str(votes_to_subtract_from_other_ranks)
                random_rank_select = random.choice(other_ranks)
                # print "        for rank " + str(random_rank_select)
                if(len(other_ranks) == 1):
                    random_votes_to_subtract = votes_to_subtract_from_other_ranks
                else:
                    random_votes_to_subtract = round(random.uniform(0,votes_to_subtract_from_other_ranks),2)
                # print "          to subtract from this: " + str(random_votes_to_subtract)
                # print "          this has? " + str(random_channel_select_in_country['ranks'][random_rank_select])
                if(random_channel_select_in_country['ranks'][random_rank_select] > random_votes_to_subtract):
                    # print "          boom"
                    random_channel_select_in_country['ranks'][random_rank_select] = round((random_channel_select_in_country['ranks'][random_rank_select] - random_votes_to_subtract),2)
                    votes_to_subtract_from_other_ranks = round((votes_to_subtract_from_other_ranks - random_votes_to_subtract),2)
                    # print "             votes remaining for next rank loop: " + str(votes_to_subtract_from_other_ranks)
                else:
                    # print "          NOPPPPEEEEE"
                    pass
                other_ranks.remove(random_rank_select)

        votes_to_distribute -= votes_to_add_to_1_rank
        channels_to_distribute_in.remove(random_channel_select)

def winner_irv(channels,country_data_to_use):
    print "\n------------- INITIATING RANKED VOTING - IRV -------------\n"
    results = {}
    for channel_obj in channels:
        results[channel_obj['name']] = 0

    channels_copied = copy.deepcopy(channels)

    for country_obj in country_data_to_use:
        this_country = country_obj['country']
        this_country_population = country_obj['useful_count']
        # print "=============="
        # print str(this_country) + " with " + str(this_country_population)

        # to handle and skip countries where all 1 ranks are 0
        non_zero_1_ranks_channels = filter(lambda c: getChannelCountryDict(c,this_country)['ranks'][1] != 0, channels_copied)
        if(len(non_zero_1_ranks_channels)):
            winner = {}
            while(not winner):
                lowest_1_rank = float('inf')
                channel_to_eliminate = {}
                for channel_obj in non_zero_1_ranks_channels:
                    if(not winner):
                        this_channel_1_ranks_in_this_country = getChannelCountryDict(channel_obj,this_country)['ranks'][1]
                        # print "    1 ranks for " + str(channel_obj['name']) + ": " + str(this_channel_1_ranks_in_this_country)
                        if(this_channel_1_ranks_in_this_country > (this_country_population/2.0)):
                            winner = channel_obj
                        else:
                            if(this_channel_1_ranks_in_this_country < lowest_1_rank):
                                lowest_1_rank = this_channel_1_ranks_in_this_country
                                channel_to_eliminate = channel_obj
                if(not winner):
                    # print "        Eliminated " + str(channel_to_eliminate['name'])
                    channel_to_eliminate_1_ranks_in_this_country = lowest_1_rank
                    non_eliminated_channels = filter(lambda c: c['name'] != channel_to_eliminate['name'], non_zero_1_ranks_channels)
                    distributeEliminatedChannelsVotes(channel_to_eliminate_1_ranks_in_this_country,non_eliminated_channels,this_country)
                    # print [c['name'] for c in non_zero_1_ranks_channels]
                    non_zero_1_ranks_channels.remove(channel_to_eliminate)


    # printChannelVotes(channels_copied)


            # print "Winner " + str(this_country) + ": " + str(winner['name'])
            results[winner['name']] += 1

    print "\nSeats distribution for " + str(len(country_data_to_use)) + " seats (countries):"
    print sorted(results.items(), key=itemgetter(1), reverse = True)
    print "\n"
    print max(results.iterkeys(), key=lambda x: results[x]) + " forms government!"
    print "\n"

def winner_ranked_borda_count(channels,country_data_to_use):
    print "\n------------- INITIATING RANKED VOTING - BORDA COUNT -------------\n"
    results = {}
    for channel_obj in channels:
        results[channel_obj['name']] = 0

    channels_copied = copy.deepcopy(channels)

    for country_obj in country_data_to_use:
        this_country = country_obj['country']
        # print "___ ___ ___ ___ ___ ___"
        # print this_country
        lowest_rank_sum = float('inf')
        winner = {}

        for channel_obj in channels_copied:
            this_channel_ranks_in_this_country = getChannelCountryDict(channel_obj,this_country)['ranks']
            # print "    " + str(channel_obj['name']) + ": " + str(this_channel_ranks_in_this_country)
            all_ranks = this_channel_ranks_in_this_country.keys()
            all_ranks_sum = sum(map(lambda r: r*this_channel_ranks_in_this_country[r], all_ranks))
            # print "    " + str(channel_obj['name']) + ": " + str(all_ranks_sum)
            if(all_ranks_sum < lowest_rank_sum):
                lowest_rank_sum = all_ranks_sum
                winner = channel_obj

        if(lowest_rank_sum > 0):
            # print "Winner " + str(this_country) + ": " + str(winner['name'])
            results[winner['name']] += 1

    print "\nSeats distribution for " + str(len(country_data_to_use)) + " seats (countries):"
    print sorted(results.items(), key=itemgetter(1), reverse = True)
    print "\n"
    print max(results.iterkeys(), key=lambda x: results[x]) + " forms government!"
    print "\n"

# def diff_in_sum_of_diagonally_opposite(c1,c2,rank,all_ranks):
#     remaining_ranks_here = filter(lambda r: r > rank, all_ranks)
#     remaining_c2_votes_sum = sum(map(lambda v: c2['ranks'][v], remaining_ranks_here))
#     # print remaining_c2_votes_sum
#     # if(c1['ranks'][rank] == remaining_c2_votes_sum):  # or, c2['ranks'][rank] == remaining_c1_votes_sum. Either condition works.
#     #     return True
#     # else:
#     #     return False
#     return (c1['ranks'][rank] - remaining_c2_votes_sum)

def subtract_from_other_channel(c1_test, c2_test, rank, lower_ranks, this_country):
    channel1_ranks_in_this_country = getChannelCountryDict(c1_test,this_country)['ranks']
    channel2_ranks_in_this_country = getChannelCountryDict(c2_test,this_country)['ranks']
    c1_votes = 0
    channel1_votes_here = channel1_ranks_in_this_country[rank]
    non_channel1_zero_ranks = filter(lambda lr: channel1_ranks_in_this_country[lr] != 0, lower_ranks)
    non_channel1_zero_ranks = sorted(non_channel1_zero_ranks, key=lambda r: channel2_ranks_in_this_country[r], reverse=True)
    # print non_channel1_zero_ranks
    for non_zero_rank in non_channel1_zero_ranks:
        to_subtract = min(channel1_votes_here, channel2_ranks_in_this_country[non_zero_rank])
        c1_votes += to_subtract
        channel1_ranks_in_this_country[rank] = round((channel1_ranks_in_this_country[rank] - to_subtract),2)
        channel1_votes_here = round((channel1_votes_here - to_subtract),2)
        channel2_ranks_in_this_country[non_zero_rank] = round((channel2_ranks_in_this_country[non_zero_rank] - to_subtract),2)

    if(channel1_votes_here):
        channel2_ranks = sorted(lower_ranks, key=lambda r: channel2_ranks_in_this_country[r], reverse=True)
        for c2_rank in channel2_ranks:
            to_subtract = min(channel1_votes_here, channel2_ranks_in_this_country[c2_rank])
            c1_votes += to_subtract
            channel1_ranks_in_this_country[rank] = round((channel1_ranks_in_this_country[rank] - to_subtract),2)
            channel1_votes_here = round((channel1_votes_here - to_subtract),2)
            channel2_ranks_in_this_country[c2_rank] = round((channel2_ranks_in_this_country[c2_rank] - to_subtract),2)

    return c1_votes

def winner_ranked_condorcet(channels,country_data_to_use):
    # channels_test = [
    #     {'name':'A','ranks':{1: 1, 2: 4, 3: 2, 4: 0}},
    #     {'name':'B','ranks':{1: 3, 2: 0, 3: 0, 4: 4}},
    #     {'name':'C','ranks':{1: 1, 2: 2, 3: 2, 4: 2}},
    #     {'name':'D','ranks':{1: 2, 2: 1, 3: 3, 4: 1}}
    # ]
    print "\n------------- INITIATING RANKED VOTING - CONDORCET -------------\n"
    results = {}
    for channel_obj in channels:
        results[channel_obj['name']] = 0

    channels_copied = copy.deepcopy(channels)
    total_channels = len(channels_copied)
    total_ranks = (channels_copied[0]['distribution'][0]['ranks']).keys()

    for country_obj in country_data_to_use:
        this_country = country_obj['country']
        # print "___ ___ ___ ___ ___ ___"
        # print this_country

        channel_winners = [{'name': c['name'], 'winner_in': 0} for c in channels_copied]
        channel_winners.append({'name': 'NO WINNER', 'winner_in': 0})

        for ci in xrange(total_channels):
            c1 = channels[ci]
            for cj in xrange((ci+1),total_channels):
                c2 = channels[cj]
                c1_test = copy.deepcopy(c1)
                c2_test = copy.deepcopy(c2)
                c1_votes = 0
                c2_votes = 0

                for rank in total_ranks:
                    # print "Rank: " + str(rank)
                    lower_ranks = filter(lambda r: r > rank, total_ranks)

                    # Channel 1:
                    c1_votes += subtract_from_other_channel(c1_test, c2_test, rank, lower_ranks, this_country)

                    # Channel 2:
                    c2_votes += subtract_from_other_channel(c2_test, c1_test, rank, lower_ranks, this_country)

                if(c1_votes > c2_votes):
                    winner = c1
                elif(c1_votes < c2_votes):
                    winner = c2
                else:
                    winner = {'name': 'NO WINNER'}

                channel_winner_obj = filter(lambda c: c['name'] == winner['name'], channel_winners)[0]
                channel_winner_obj['winner_in'] += 1

                # if this_country == 'India':
                #     print str(c1['name']) + ": " + str(c1_votes)
                #     print str(c2['name']) + ": " + str(c2_votes)
                #     print "Winner: " + str(winner['name'])
                #     print "\n"

        # print channel_winners
        ultimate_winner = max(filter(lambda c: c['name'] != 'NO WINNER', channel_winners), key=lambda w:w['winner_in'])
        # print "----------------\nUltimate winner: " + str(ultimate_winner['name'])
        results[ultimate_winner['name']] += 1

    print "\nSeats distribution for " + str(len(country_data_to_use)) + " seats (countries):"
    print sorted(results.items(), key=itemgetter(1), reverse = True)
    print "\n"
    print max(results.iterkeys(), key=lambda x: results[x]) + " forms government!"
    print "\n"


def votes_distribution_exclusive(channels,country_data_to_use):
    subs_in_home_country_percentage = 20                    # x = 20 %
    subs_in_home_language_countries_percentage = 50         # y = 50 %
    # rest in rest

    for channel_obj in channels:
        channel_country = channel_obj['country']
        channel_language = channel_obj['language']
        channel_subs = channel_obj['subs']
        channel_obj['distribution'] = []
        # total_voters = sum(x['count'] for x in country_data_to_use)

        if(channel_country in map(lambda x: x['country'], country_data_to_use)):
            subs_in_home_country = channel_obj['subs'] * subs_in_home_country_percentage/100
            channel_obj['distribution'].append({'country': channel_country, 'count': round((subs_in_home_country * pow(10,-6)),2)})
            channel_subs -= subs_in_home_country
            # total_voters = sum(x['count'] for x in filter(lambda y: y['country'] != channel_country, country_data_to_use))
            # if(channel_obj['name'] == 'T-Series'):
            #     print subs_in_home_country

        non_home_countries = filter(lambda y: y['country'] != channel_country, country_data_to_use)
        covered_countries = []
        non_home_countries_count = map(lambda country_obj: {'country': country_obj['country'], 'language_count': country_obj['languages'][channel_language] * country_obj['count'] / 100}, non_home_countries)
        # if(channel_obj['name'] == 'T-Series'):
        #     print non_home_countries_count

        denominator_non_home_countries = sum(z['language_count'] for z in non_home_countries_count)
        # if(channel_obj['name'] == 'T-Series'):
        #     print denominator_non_home_countries
        subs_in_home_language_countries = channel_obj['subs'] * subs_in_home_language_countries_percentage/100
        for country_obj in non_home_countries_count:
            subs_in_this_home_language_country = subs_in_home_language_countries * (country_obj['language_count']/denominator_non_home_countries)
            # if(channel_obj['name'] == 'T-Series'):
            #     print country_obj['country'] + " has: "
            #     print subs_in_this_home_language_country
            if(subs_in_this_home_language_country > 0):
                channel_obj['distribution'].append({'country': country_obj['country'], 'count': round((subs_in_this_home_language_country * pow(10,-6)),2)})
                covered_countries.append(country_obj['country'])
        channel_subs -= subs_in_home_language_countries

        remaining_countries = filter(lambda f: f['country'] not in covered_countries and f['country'] != channel_country, country_data_to_use)
        total_remaining_voters = sum(x['count'] for x in remaining_countries)

        for country_obj in remaining_countries:
            # print country_obj
            subs_in_this_country = (channel_subs * (country_obj['count'] / total_remaining_voters) * pow(10,-6))

            # * (channel_obj['subs']/total_votes)
            channel_obj['distribution'].append({'country': country_obj['country'], 'count': round(subs_in_this_country,2)})
            # (80 * 10^6) * [(167.4 * 10^6)/(total * 10^6)] = (80 * 10^6) * [167.4/total]

    count = 0
    for o in country_data_to_use:
        count += o['count']
        print o
    print count

    printChannelVotes(channels)
    printCountryVotes(country_data_to_use, channels)


def winner_approval_rating(all_channels,all_countries):
    print "// constructing voter population..."
    votes_distribution_exclusive(all_channels,all_countries)

    print "\n------------- INITIATING APPROVAL VOTING -------------\n"
    results = {}
    for channel_obj in all_channels:
        results[channel_obj['name']] = 0

    for country_obj in all_countries:
        this_country = country_obj['country']
        # print "________________________"
        # print this_country
        max_votes_in_this_country = 0
        winner = {}

        total_votes_in_country = country_obj['voting_population']
        for channel_obj in all_channels:
            this_channel_base_votes_in_this_country = getChannelCountryDict(channel_obj,this_country)['count']
            difference_to_total = total_votes_in_country - this_channel_base_votes_in_this_country

            this_channel_actual_votes_in_this_country = this_channel_base_votes_in_this_country + random.uniform(-difference_to_total,difference_to_total)
            # print "    " + str(channel_obj['name']) + ": " + str(this_channel_actual_votes_in_this_country)

            if(this_channel_actual_votes_in_this_country > max_votes_in_this_country):
                max_votes_in_this_country = this_channel_actual_votes_in_this_country
                winner = channel_obj
        # print "Total population involved in voting: " + str(total_votes_in_country)

        if(winner):
            print "Winner " + str(this_country) + ": " + str(winner['name'])
            results[winner['name']] += 1

    print "\nSeats distribution for " + str(len(all_countries)) + " seats (countries):"
    print sorted(results.items(), key=itemgetter(1), reverse = True)
    print "\n"
    print max(results.iterkeys(), key=lambda x: results[x]) + " forms government!"
    print "\n"


def shapeCountryPopulationDataAccordingToLanguages(countries):
    # Use language %ages in country data to get exact NUMBER of people per language.
    # Add all these NUMBERS. These are our useful population (since only they speak the languages we are concerned with)
    # Find and remember %age share of each language from the previous total. This would be useful after scaling down ahead.
    # SCALE this total number down to match sum of all subs.
    # Use earlier %age remembered data to find exact NUMBER of people per language in this scaled down number.

    for country_obj in countries:
        country_languages = country_obj['languages'].keys()
        subset_of_language_data = {}
        total_size_of_subset = 0
        for language in country_languages:
            this_language_population = round((country_obj['count'] * (country_obj['languages'][language]) / 100),2)
            subset_of_language_data[language] = this_language_population
            total_size_of_subset += this_language_population

        country_obj['useful_count'] = total_size_of_subset
        country_obj['useful_languages'] = subset_of_language_data

        if(total_size_of_subset > 0):
            useful_languages = country_obj['useful_languages'].keys()
            for u_language in useful_languages:
                country_obj['useful_languages'][u_language] = round(((country_obj['useful_languages'][u_language]/total_size_of_subset) * 100),2)

    useful_youtube_population = sum(c['useful_count'] for c in countries)           # youtube population that speaks only relevant languages (but, this is > total subs count)
    # print useful_youtube_population

    temp_copy = copy.deepcopy(countries)                                            # so....scaling it down....
    useful_scaled_down = map(lambda x: changeDictValue(x,'useful_count', round((x['useful_count'] * (total_votes_million/useful_youtube_population)),2) ), temp_copy)

    # printCountryWiseDistribution(useful_scaled_down)
    print "Useful population: " + str(sum(c['useful_count'] for c in useful_scaled_down))                        # should be = total subs count
    return useful_scaled_down

total_monthly_2016_top_15_countries = [
    # Language data (in percentages) from: (default source for EN: https://en.wikipedia.org/wiki/List_of_countries_by_English-speaking_population, for PR: https://en.wikipedia.org/wiki/Geographical_distribution_of_Portuguese_speakers)
    {'country': 'US', 'languages': {'EN': 75.8 , 'HI': 0.26 , 'PR': 0.25 }, 'count': 167.4},                            # FIRST LANGUAGE
    # https://en.wikipedia.org/wiki/Languages_of_the_United_States
    {'country': 'Brazil', 'languages': {'EN': 0.14 , 'HI': 0 , 'PR': 98 }, 'count': 69.5},                              # FIRST LANGUAGE
    # https://en.wikipedia.org/wiki/List_of_countries_by_English-speaking_population (2012)
    {'country': 'Russia', 'languages': {'EN': 5.48 , 'HI': 0 , 'PR': 0 }, 'count': 47.4},
    # https://en.wikipedia.org/wiki/List_of_countries_by_English-speaking_population (Russian Census 2010 included)
    {'country': 'Japan', 'languages': {'EN': 0 , 'HI': 0 , 'PR': 0 }, 'count': 46.8},
    # Umm...
    {'country': 'India', 'languages': {'EN': 0.02, 'HI': 43.63, 'PR': 0}, 'count': 41.2},                               # FIRST LANGUAGE
    # 2011 Census of India (https://en.wikipedia.org/wiki/2011_Census_of_India#Language_demographics)
    {'country': 'UK', 'languages': {'EN': 97.74 , 'HI': 0 , 'PR': 0.2 }, 'count': 35.6},
    # 2011 Census of UK (Punjabi is 0.5%, but since we're only looking at Hindi, it's 0)
    {'country': 'Germany', 'languages': {'EN': 56, 'HI': 0, 'PR': 0.1 }, 'count': 31.3},
    # EN: Special EUROBAROMETER 243 (2006) (http://ec.europa.eu/commfrontoffice/publicopinion/archives/ebs/ebs_243_en.pdf)
    # EN: Same in Special EUROBAROMETER 386 (2012)
    {'country': 'France', 'languages': {'EN': 39 , 'HI': 0 , 'PR': 1.3 }, 'count': 30.3},
    # Special EUROBAROMETER 386 (2012)
    {'country': 'Mexico', 'languages': {'EN': 12.9 , 'HI': 0 , 'PR': 0 }, 'count': 29.4},
    {'country': 'Turkey', 'languages': {'EN': 0 , 'HI': 0 , 'PR': 0 }, 'count': 28.8},
    # Special EUROBAROMETER 243 (2006)
    {'country': 'Argentina', 'languages': {'EN': 6.52 , 'HI': 0 , 'PR': 0 }, 'count': 26.1},
    {'country': 'Poland', 'languages': {'EN': 37 , 'HI': 0 , 'PR': 0 }, 'count': 25.3},
    {'country': 'Canada', 'languages': {'EN': 86.21 , 'HI': 0.32 , 'PR': 0.64 }, 'count': 22.8},
    # https://en.wikipedia.org/wiki/Languages_of_Canada
    {'country': 'Vietnam', 'languages': {'EN': 0 , 'HI': 0 , 'PR': 0 }, 'count': 22},
    # Umm^2
    {'country': 'Spain', 'languages': {'EN': 22 , 'HI': 0 , 'PR': 0.2 }, 'count': 18.7}
 ]

channels = [
    {
        'name':'PewDiePie',
        'country': 'US',
        'language': 'EN',
        'subs': 80035336.0,
    },
    {
        'name':'T-Series',
        'country': 'India',
        'language': 'HI',
        'subs': 79243848.0,
    },
    {
        'name':'5-Minute Crafts',
        'country': 'US',
        'language': 'EN',
        'subs': 46219121.0,
    },
    {
        'name':'Canal KondZilla',
        'country': 'Brazil',
        'language': 'PR',
        'subs': 45110566.0,
    },
    {
        'name':'Justin Bieber',
        'country': 'Canada',
        'language': 'EN',
        'subs': 42733430.0,
    }
]

total_youtube_population = sum(x['count'] for x in total_monthly_2016_top_15_countries)
# print "Total YouTube population: " + str(total_youtube_population) + "M"
total_votes = sum(y['subs'] for y in channels)
total_votes_million = round((total_votes * pow(10,-6)),2)
print "Total sub count: " + str(total_votes_million) + "M"

for channel_obj in channels:
    channel_obj['distribution'] = []

    channels_length = len(channels)
    channel_ranks = {}
    for i in xrange(1,channels_length+1):
        channel_ranks[i] = 0

    for country_obj in total_monthly_2016_top_15_countries:
        channel_obj['distribution'].append({'country': country_obj['country'], 'count': 0, 'ranks': copy.copy(channel_ranks)})

# print channels

# scaled_up?

# Sum of youtube users across all countries comes GREATER THAN sum of all channel subscribers. This doesn't cause any problem for Approval Voting (vote more than one candidate), since we're splitting each channel's sub base into proportions across countries based on these youtube users' proportions across countries. However, for systems where ONLY one candidate is allowed, we'll have to split the COUNTRY USER BASE in proportion to the channel's sub proportions. This leads to an inconsistency. We assume each channel's default sub base (i.e. for ex: 80M for PewDiePie) to be MUTUALLY EXCLUSIVE (voting only one candidate), i.e. 80M are ONLY PewDiePie's subs. Under this assumption, the addition of all subs across all channels should be equal to total youtube user population, which is not the case as stated before. Therefore, we scale down these country wise populations (in their respective proportions) so that the new sum comes equal to total subscribers.
# ********* EDIT **********: This is too simplistic, and probably stright up WRONG, refer TODO file for more nuances.
# temp_copy = copy.deepcopy(total_monthly_2016_top_15_countries)
# scaled_down_total_monthly_2016_top_15_countries = map(lambda x: changeDictValue(x,'count', round((x['count'] * (total_votes_million/total_youtube_population)),2) ), temp_copy)

useful_country_data = shapeCountryPopulationDataAccordingToLanguages(total_monthly_2016_top_15_countries)

votes_distribution_fptp(channels, useful_country_data)
# winner_fptp(channels, useful_country_data)
votes_distribution_ranked_voting(channels, useful_country_data)
# printChannelVotes(channels)
winner_irv(channels,useful_country_data)
winner_ranked_borda_count(channels, useful_country_data)
winner_ranked_condorcet(channels,useful_country_data)
