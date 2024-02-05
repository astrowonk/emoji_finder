drop view if exists combined_emoji;

CREATE VIEW combined_emoji as
select
	word,
	emoji,
	rank_of_search,
	label,
	text,
	version
from
	lookup l
	left join emoji_df e on l.word_lookup = e.idx
	/* combined_emoji(word,emoji,rank_of_search,label,text,version) */
;

CREATE INDEX if not exists emoji_lookup on lookup(word);

CREATE INDEX if not exists emoji_idx on emoji_df(idx);

CREATE INDEX if not exists myindex on lookup(word);

create index if not exists emoji_label on emoji_df(label);