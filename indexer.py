import sys
from token_streamer import TokenStreamer
from token_streamer import CorpusStatsStreamer
from token_streamer import DocumentSentimentStreamer
from os import remove
import time


def create_index():

    start_time = time.time()

    i, blocks = 0, []
    base_stream = TokenStreamer()
    stats_stream = CorpusStatsStreamer(base_stream)
    stream = DocumentSentimentStreamer(stats_stream)

    while stream.has_next():
        d, p = spimi_invert(stream, i)
        i += 1
        blocks.append([d, p])
    merge_blocks(blocks)

    print 'Index created in %d seconds.' % (time.time() - start_time)


def spimi_invert(stream, i):
    print 'Inverting block ' + str(i) + '...'

    # instantiate dictionary_block
    # keys in dictionary block are terms
    # values are list of tuples of doc_id of of doc containing the term and number times term appears in doc
    dictionary_block = {}

    while sys.getsizeof(dictionary_block)/float(1024)/float(1024) < 2.0:
        token_id_pair = stream.next()

        # if nothing is returned then end early
        if not token_id_pair:
            break

        token, doc_id = token_id_pair[0], token_id_pair[1]

        if dictionary_block.has_key(token):
            # if last doc in postings list is different
            if dictionary_block[token][-1][0] != doc_id:
                dictionary_block[token].append([doc_id, 1])
            else:
                dictionary_block[token][-1][1] += 1
        else:
            dictionary_block[token] = [[doc_id, 1]]
    return write_block_to_disk(dictionary_block, i)


def write_block_to_disk(block, i):

    # sort dictionary keys in block
    keys = block.keys()
    keys.sort()

    # open separate files to write dictionary and postings
    dict_file_name = 'block_'+str(i)+'.dict'
    postings_file_name = 'block_'+str(i)+'.postings'
    dict_file = open(dict_file_name,'w')
    postings_file = open(postings_file_name, 'w')

    for key in keys:
        postings_list = block[key]

        # write each key to a new line in dictionary file
        dict_file.write(key+'\n')
        for posting in postings_list:
            # write each posting to corresponding line in postings file
            postings_file.write(','.join(map(str, posting)))
            postings_file.write(';')
        postings_file.write('\n')

    # close files
    dict_file.close()
    postings_file.close()

    # return file names to be reopened later
    return dict_file_name, postings_file_name


def merge_blocks(block_names):
    print 'Merging blocks...'

    # create new files for final merged dictionary and postings
    final_dict = open('reuters.dict', 'w')
    final_postings = open('reuters.postings', 'w')

    # initialize lists
    dict_read_buffer = []
    post_read_buffer = []
    blocks = []

    # open all files and fill buffer
    for dict_file, post_file in block_names:
        d = open(dict_file, 'r')
        p = open(post_file, 'r')
        blocks.append([d,p])
        dict_read_buffer.append(d.readline())
        post_read_buffer.append(p.readline()[:-1])

    # loop until all files are removed from blocks
    while blocks:

        # determine smallest term in all buffers
        min_term = min(dict_read_buffer)

        # write min term to file and the current position in the postings file (pointer to line)
        final_dict.write(str(min_term)[:-1]+','+str(final_postings.tell())+'\n')

        # for every block with min term, write postings to file and update read buffer
        # postings are already in order
        kill_list = []
        posting_string = ''
        for i,term in enumerate(dict_read_buffer):
            if term == min_term:
                # build string of postings
                posting_string += post_read_buffer[i]

                # update buffers
                dict_read_buffer[i] = blocks[i][0].readline()
                post_read_buffer[i] = blocks[i][1].readline()[:-1]

            # close emptied files, add to list to remove
            if dict_read_buffer[i] == '':
                blocks[i][0].close()
                blocks[i][1].close()
                kill_list.append(i)

        # compress postings list and write to file
        postings_list = parse_postings_string(posting_string)
        postings_list = compress_postings_list(postings_list)
        final_postings.write(postings_list_to_string(postings_list))
        final_postings.write('\n')

        # remove emptied files from blocks and remove corresponding buffers
        blocks = [x for i,x in enumerate(blocks) if i not in kill_list]
        dict_read_buffer = [x for i,x in enumerate(dict_read_buffer) if i not in kill_list]
        post_read_buffer = [x for i,x in enumerate(post_read_buffer) if i not in kill_list]

    # delete all old files
    for old_dict, old_post in block_names:
        remove(old_dict)
        remove(old_post)


def parse_postings_string(postings_string):
    # split postings list string into list of separate postings strings
    postings_list = postings_string[:-1].split(';')

    # split each posting into its 2 components
    postings_list = map(lambda x: x.split(','), postings_list)

    # cast each component to int
    postings_list = map(lambda x: map(lambda y: int(y), x), postings_list)

    return postings_list


def postings_list_to_string(postings_list):
    # cast postings list's posting's components to string
    postings_list = map(lambda x: map(lambda y: str(y), x), postings_list)

    # join into ,; separated string and return
    return ';'.join(map(lambda x: ','.join(x), postings_list))


def compress_postings_list(postings_list):
    # merge entries that have identical doc_ids
    # since list is sorted, they will be adjacent
    last_doc_id = 0
    last_i = -1
    kill_list = []
    for i, pair in enumerate(postings_list):
        if postings_list[i][0] == last_doc_id:
            postings_list[last_i][1] += postings_list[i][1]
            kill_list.append(i)
        else:
            last_doc_id = postings_list[i][0]
            last_i = i
    postings_list = [x for i, x in enumerate(postings_list) if i not in kill_list]

    # only store difference from previous doc_id
    base_amount = 0
    for posting in postings_list:
        posting[0], base_amount = posting[0] - base_amount, posting[0]

    # don't store term frequency if it is 1
    for i, posting in enumerate(postings_list):
        if posting[1] == 1:
            postings_list[i] = [posting[0]]

    return postings_list

if __name__ == '__main__':
    create_index()