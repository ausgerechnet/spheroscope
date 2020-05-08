INSERT INTO users (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO queries (author_id, name, query, anchors, regions)
VALUES
  (1, 'test query', '@0:[::]\"last\" @1:[::]\"week|month|year\" \",\"? <np>@2:[::][]*</np> <vp>[]* [pos_ner=\"VBD\"]</vp> (<np>[]*</np> | <vp>[]*</vp> | <pp>[]*</pp> | /be_ap[] | <advp>[]*</advp>)+@3:[::]', '[[0, 0, null null], [1, 0, null, null], [2, 0, null, null], [3, -1, null, null]]', '[[0, 1, "0", null], [2, 3, "1", null]]');
