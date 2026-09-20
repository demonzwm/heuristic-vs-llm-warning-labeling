## Shot 1

Tool: csa
        Rule: Dereference of null pointer
        CWE: CWE-476
        Function: <global>
        Warning Message: Logic error: Dereference of null pointer

        Stage1 Semantic Prediction: TP
        Stage1 Semantic Confidence: High
        Stage1 Supporting Reasoning:
        The pointer 'earliest' is initialized to NULL and only assigned a non-NULL value inside the while loop if a timer event satisfies the condition. If no timer event satisfies the condition (e.g., all events have id == AE_DELETED_EVENT_ID), 'earliest' remains NULL. The loop does not guarantee that 'earliest' is set. After the loop, the code dereferences 'earliest' without a null check, leading to a null pointer dereference. The earlier null check on 'te' does not protect 'earliest'.

        CWE Reasoning Schema: CWE-476

        Code Context:
        ```c
        static int64_t usUntilEarliestTimer(aeEventLoop *eventLoop) {
    aeTimeEvent *te = eventLoop->timeEventHead;
    if (te == NULL) return -1;
    aeTimeEvent *earliest = NULL;
    while (te) {
        if ((!earliest || te->when < earliest->when) && te->id != AE_DELETED_EVENT_ID)
            earliest = te;
        te = te->next;
    }
    monotime now = getMonotonicUs();
    return (now >= earliest->when) ? 0 : earliest->when - now;  // The line where the warning is located
}
        ```

        DEFECT HYPOTHESIS
        A real null-dereference exists if `earliest` can remain NULL after the loop and the return expression can still reach `earliest->when`.

        Structured Verification:
        NULL Source / Propagation: `earliest` starts as NULL and only becomes non-NULL inside the loop body.
Guard / Safety Constraint: `if (te == NULL) return -1;` only proves the list head exists. It does not prove any node satisfies `te->id != AE_DELETED_EVENT_ID`.
Path Feasibility: A feasible path exists where every visited node is deleted, so the loop terminates with `earliest` still NULL.
Dereference Reachability: The return expression dereferences `earliest->when` immediately after the loop with no intervening guard.

        Defect Hypothesis Status: SUPPORTED

        SAFETY HYPOTHESIS
        The warning is a false positive if the loop structure guarantees that at least one non-deleted timer always assigns `earliest` before the dereference.

        Structured Verification:
        The safety hypothesis fails because the visible code never enforces the premise that some non-deleted timer must exist. The earlier check protects `te`, not `earliest`.

        Safety Hypothesis Status: REFUTED

        WARNING-EVOLUTION EVIDENCE ASSESSMENT
        Structured Warning-Evolution Evidence:
- matched: yes
- matching method: Location-based match
- matched version: 8.0.2
- matched child warning: {'file_path': 'src/ae.c', 'rule_id': 'Dereference of null pointer', 'cwe': 'CWE-476', 'function_name': 'usUntilEarliestTimer'}
- location threshold: 3
- later versions checked: Unavailable
- SCA reports checked: Unavailable
- original evolution state: Unavailable
- trace completeness: Unavailable
- evidence reliability: HIGH

        Evolution Analysis:
        The later-version correspondence is a historical observation about warning persistence. It does not prove the current dereference is safe. The visible semantic path is still sufficient to keep the defect hypothesis stronger.

        CROSS-EVIDENCE RESOLUTION
        The defect hypothesis is supported by a concrete same-slice path: `earliest` may remain NULL, no safety constraint blocks that path, and the dereference is reachable immediately after the loop. The historical warning correspondence does not override this semantic evidence.

        Final Label: TP

## Shot 2

Tool: codeql
        Rule: cpp/inconsistent-null-check
        CWE: CWE-476
        Function: <global>
        Warning Message: The result of this call to find_win_by_nr_or_id is not checked for null, but 90% of calls to find_win_by_nr_or_id check for null.

        Stage1 Semantic Prediction: TP
        Stage1 Semantic Confidence: High
        Stage1 Supporting Reasoning:
        The function find_win_by_nr_or_id can return NULL (e.g., if the window number or ID is invalid). Its return value is assigned to wp->w_popup_prop_win without a null check before being used in the subsequent call to find_prop_type_id(str, wp->w_popup_prop_win->w_buffer). Although there is a later check win_valid_any_tab(wp->w_popup_prop_win), this check occurs after the dereference in find_prop_type_id. The null check does not protect the earlier dereference. Therefore, a null pointer dereference is possible on the path where find_win_by_nr_or_id returns NULL.

        CWE Reasoning Schema: CWE-476

        Code Context:
        ```c
        // ========== Sliced Code ==========

    static void
apply_move_options(win_T *wp, dict_T *d)
{
    int		nr;
    char_u	*str;
    dictitem_T	*di;
    if ((nr = dict_get_number_def(d, "minwidth", -1)) >= 0)
	wp->w_minwidth = nr;
    if ((nr = dict_get_number_def(d, "minheight", -1)) >= 0)
	wp->w_minheight = nr;
    if ((nr = dict_get_number_def(d, "maxwidth", -1)) >= 0)
	wp->w_maxwidth = nr;
    if ((nr = dict_get_number_def(d, "maxheight", -1)) >= 0)
	wp->w_maxheight = nr;
    nr = popup_options_one(d, (char_u *)"line");
    if (nr != MAXCOL)
	wp->w_wantline = nr;
    nr = popup_options_one(d, (char_u *)"col");
    if (nr != MAXCOL)
	wp->w_wantcol = nr;
    nr = dict_get_bool(d, "fixed", -1);
    if (nr != -1)
	wp->w_popup_fixed = nr != 0;
    {
	poppos_T ppt = get_pos_entry(d, TRUE);
	if (ppt != POPPOS_NONE)
	    wp->w_popup_pos = ppt;
    }
    str = dict_get_string(d, "textprop", FALSE);
    if (str != NULL)
    {
	wp->w_popup_prop_type = 0;
	if (*str != NUL)
	{
	    wp->w_popup_prop_win = curwin;
	    di = dict_find(d, (char_u *)"textpropwin", -1);
	    if (di != NULL)
	    {
		wp->w_popup_prop_win = find_win_by_nr_or_id(&di->di_tv);  // The line where the warning is located
		if (!win_valid_any_tab(wp->w_popup_prop_win))
		    wp->w_popup_prop_win = curwin;
	    }

	    nr = find_prop_type_id(str, wp->w_popup_prop_win->w_buffer);
	    if (nr <= 0)
		nr = find_prop_type_id(str, NULL);
	    if (nr <= 0)
		semsg(_(e_invalid_argument_str), str);
	    else
		wp->w_popup_prop_type = nr;
	}
    }
    di = dict_find(d, (char_u *)"textpropid", -1);
    if (di != NULL)
	wp->w_popup_prop_id = dict_get_number(d, "textpropid");
}


// ========== Called Function Definitions ==========

// Macro: _ from src/GvimExt/gvimext.cpp (line 182)
# define _(x)	    x

// Function: dict_find from src/dict.c (lines 622-653)
dictitem_T *
dict_find(dict_T *d, char_u *key, int len)
{
#define AKEYLEN 200
    char_u	buf[AKEYLEN];
    char_u	*akey;
    char_u	*tofree = NULL;
    hashitem_T	*hi;

    if (d == NULL)
	return NULL;
    if (len < 0)
	akey = key;
    else if (len >= AKEYLEN)
    {
	tofree = akey = vim_strnsave(key, len);
	if (akey == NULL)
	    return NULL;
    }
    else
    {
	// Avoid a malloc/free by using buf[].
	vim_strncpy(buf, key, len);
	akey = buf;
    }

    hi = hash_find(&d->dv_hashtab, akey);
    vim_free(tofree);
    if (HASHITEM_EMPTY(hi))
	return NULL;
    return HI2DI(hi);
}

// Function: dict_get_bool from src/dict.c (lines 751-760)
varnumber_T
dict_get_bool(dict_T *d, char *key, int def)
{
    dictitem_T	*di;

    di = dict_find(d, (char_u *)key, -1);
    if (di == NULL)
	return def;
    return tv_get_bool(&di->di_tv);
}

// Function: dict_get_number from src/dict.c (lines 705-709)
varnumber_T
dict_get_number(dict_T *d, char *key)
{
    return dict_get_number_def(d, key, 0);
}

// Function: dict_get_number_def from src/dict.c (lines 715-724)
varnumber_T
dict_get_number_def(dict_T *d, char *key, int def)
{
    dictitem_T	*di;

    di = dict_find(d, (char_u *)key, -1);
    if (di == NULL)
	return def;
    return tv_get_number(&di->di_tv);
}

// Function: dict_get_string from src/dict.c (lines 686-699)
char_u *
dict_get_string(dict_T *d, char *key, int save)
{
    dictitem_T	*di;
    char_u	*s;

    di = dict_find(d, (char_u *)key, -1);
    if (di == NULL)
	return NULL;
    s = tv_get_string(&di->di_tv);
    if (save && s != NULL)
	s = vim_strsave(s);
    return s;
}

// Function: find_prop_type_id from src/textprop.c (lines 78-86)
int
find_prop_type_id(char_u *name, buf_T *buf)
{
    proptype_T *pt = find_prop_type(name, buf);

    if (pt == NULL)
	return 0;
    return pt->pt_id;
}

// Function: find_win_by_nr_or_id from src/evalwindow.c (lines 208-216)
win_T *
find_win_by_nr_or_id(typval_T *vp)
{
    int	nr = (int)tv_get_number_chk(vp, NULL);

    if (nr >= LOWEST_WIN_ID)
	return win_id2wp(tv_get_number(vp));
    return find_win_by_nr(vp, NULL);
}

// Function: get_pos_entry from current file (lines 463-479)
static poppos_T
get_pos_entry(dict_T *d, int give_error)
{
    char_u  *str = dict_get_string(d, "pos", FALSE);
    int	    nr;

    if (str == NULL)
	return POPPOS_NONE;

    for (nr = 0; nr < (int)ARRAY_LENGTH(poppos_entries); ++nr)
	if (STRCMP(str, poppos_entries[nr].pp_name) == 0)
	    return poppos_entries[nr].pp_val;

    if (give_error)
	semsg(_(e_invalid_argument_str), str);
    return POPPOS_NONE;
}

// Function: popup_options_one from current file (lines 53-93)
static int
popup_options_one(dict_T *dict, char_u *key)
{
    dictitem_T	*di;
    char_u	*val;
    char_u	*s;
    char_u	*endp;
    int		n = 0;

    di = dict_find(dict, key, -1);
    if (di == NULL)
	return MAXCOL;

    val = tv_get_string(&di->di_tv);
    if (STRNCMP(val, "cursor", 6) != 0)
	return dict_get_number_check(dict, key);

    setcursor_mayforce(TRUE);
    s = val + 6;
    if (*s != NUL)
    {
	endp = s;
	if (*skipwhite(s) == '+' || *skipwhite(s) == '-')
	    n = strtol((char *)s, (char **)&endp, 10);
	if (endp != NULL && *skipwhite(endp) != NUL)
	{
	    semsg(_(e_invalid_expression_str), val);
	    return 0;
	}
    }

    if (STRCMP(key, "line") == 0)
	n = screen_screenrow() + 1 + n;
    else // "col"
	n = screen_screencol() + 1 + n;

    // Zero means "not set", use -1 instead.
    if (n == 0)
	n = -1;
    return n;
}

// Function: semsg from src/message.c (lines 801-819)
int
semsg(const char *s, ...)
{
    // Skip this if not giving error messages at the moment.
    if (emsg_not_now())
	return TRUE;

    if (IObuff == NULL)
	// Very early in initialisation and already something wrong, just
	// give the raw message so the user at least gets a hint.
	return emsg_core(s);

    va_list ap;

    va_start(ap, s);
    vim_vsnprintf((char *)IObuff, IOSIZE, s, ap);
    va_end(ap);
    return emsg_core((char *)IObuff);
}

// Function: win_valid_any_tab from src/window.c (lines 1664-1686)
int
win_valid_any_tab(win_T *win)
{
    win_T	*wp;
    tabpage_T	*tp;

    if (win == NULL)
	return FALSE;
    FOR_ALL_TABPAGES(tp)
    {
	FOR_ALL_WINDOWS_IN_TAB(tp, wp)
	{
	    if (wp == win)
		return TRUE;
	}
#ifdef FEAT_PROP_POPUP
	FOR_ALL_POPUPWINS_IN_TAB(tp, wp)
	    if (wp == win)
		return TRUE;
#endif
    }
    return win_valid_popup(win);
}
        ```

        DEFECT HYPOTHESIS
        A real null-dereference exists if `find_win_by_nr_or_id()` can return NULL and `wp->w_popup_prop_win->w_buffer` is then used before any effective guard.

        Structured Verification:
        NULL Source: `find_win_by_nr_or_id()` can return NULL through `find_win_by_nr()` / `win_id2wp()`.
Defect Path Candidate: Stage1 points to the later call `find_prop_type_id(str, wp->w_popup_prop_win->w_buffer)`.
Counter-Evidence Check: The visible slice also contains `if (!win_valid_any_tab(wp->w_popup_prop_win)) wp->w_popup_prop_win = curwin;`.

        Defect Hypothesis Status: REFUTED

        SAFETY HYPOTHESIS
        The warning is a false positive if the visible code or called-function semantics show that the fallback logic prevents the dereference from happening on a NULL window pointer.

        Structured Verification:
        Guard / Safety Constraint: `win_valid_any_tab()` is visible and is used as the immediate fallback gate for the candidate pointer.
Path Feasibility: Before the later field access is used as a buffer argument, the code can reset `wp->w_popup_prop_win` to `curwin`, which is the safety explanation Stage1 did not fully compare against the defect hypothesis.
Resolution Predicate: The decisive question is not whether the callee may return NULL, but whether the visible fallback path prevents that NULL from surviving to the dangerous use.

        Safety Hypothesis Status: SUPPORTED

        WARNING-EVOLUTION EVIDENCE ASSESSMENT
        Structured Warning-Evolution Evidence:
- matched: yes
- matching method: Location-based match
- matched version: 9.1.0790
- matched child warning: {'file_path': 'src/popupwin.c', 'rule_id': 'cpp/poorly-documented-function', 'function_name': 'f_popup_getoptions'}
- location threshold: 3
- later versions checked: Unavailable
- SCA reports checked: Unavailable
- original evolution state: Unavailable
- trace completeness: Unavailable
- evidence reliability: HIGH

        Evolution Analysis:
        The later-version correspondence shows that a related warning persisted historically, but it does not answer the current ordering and fallback question. The final resolution still comes from the visible safety path in the current slice.

        CROSS-EVIDENCE RESOLUTION
        The semantic defect story depends on a NULL window pointer reaching the later buffer access unchanged. The visible fallback logic provides a stronger same-slice safety explanation, so the defect hypothesis is not the better-supported conclusion here.

        Final Label: FP

## Shot 3

Tool: codeql
        Rule: cpp/inconsistent-null-check
        CWE: CWE-476
        Function: fill_bitmap_commit
        Warning Message: The result of this call to prio_queue_get is not checked for null, but 71% of calls to prio_queue_get check for null.

        Stage1 Semantic Prediction: FP
        Stage1 Semantic Confidence: High
        Stage1 Supporting Reasoning:
        The call to prio_queue_get is inside a while loop that checks queue->nr before each iteration. The loop condition ensures that the queue is non-empty when prio_queue_get is called. Since prio_queue_get returns NULL only when queue->nr is 0, and the loop guarantees queue->nr > 0, the return value is never NULL. Therefore, the pointer c is always non-null at the dereference sites.

        CWE Reasoning Schema: CWE-476

        Code Context:
        ```c
        // ========== Sliced Code ==========

static int fill_bitmap_commit(struct bitmap_writer *writer,
			      struct bb_commit *ent,
			      struct commit *commit,
			      struct prio_queue *queue,
			      struct prio_queue *tree_queue,
			      struct bitmap_index *old_bitmap,
			      const uint32_t *mapping)
{
	prio_queue_put(queue, commit);
	while (queue->nr) {
		struct commit *c = prio_queue_get(queue);  // The line where the warning is located
		if (old_bitmap && mapping) {
			struct bitmap *remapped = bitmap_new();
			if (commit->object.flags & BITMAP_PSEUDO_MERGE)
				old = pseudo_merge_bitmap_for_commit(old_bitmap, c);
			else
				old = bitmap_for_commit(old_bitmap, c);
			if (old && !rebuild_bitmap(mapping, old, remapped)) {
				bitmap_or(ent->bitmap, remapped);
				bitmap_free(remapped);
				if (commit->object.flags & BITMAP_PSEUDO_MERGE)
					reused_pseudo_merge_bitmaps_nr++;
				else
					reused_bitmaps_nr++;
			}
			bitmap_free(remapped);
		}
		if (!(c->object.flags & BITMAP_PSEUDO_MERGE)) {
			pos = find_object_pos(writer, &c->object.oid, &found);
			if (!found)
				return -1;
			bitmap_set(ent->bitmap, pos);
			prio_queue_put(tree_queue,
				       repo_get_commit_tree(the_repository, c));
		}
		for (p = c->parents; p; p = p->next) {
			pos = find_object_pos(writer, &p->item->object.oid,
					      &found);
			if (!found)
				return -1;
			if (!bitmap_get(ent->bitmap, pos)) {
				prio_queue_put(queue, p->item);
			}
		}
	}
	while (tree_queue->nr) {
		if (fill_bitmap_tree(writer, ent->bitmap,
				     prio_queue_get(tree_queue)) < 0)
			return -1;
	}
}


// ========== Called Function Definitions ==========

// Function: bitmap_for_commit from pack-bitmap.c (lines 900-918)
struct ewah_bitmap *bitmap_for_commit(struct bitmap_index *bitmap_git,
				      struct commit *commit)
{
	khiter_t hash_pos = kh_get_oid_map(bitmap_git->bitmaps,
					   commit->object.oid);
	if (hash_pos >= kh_end(bitmap_git->bitmaps)) {
		struct stored_bitmap *bitmap = NULL;
		if (!bitmap_git->table_lookup)
			return NULL;

		/* this is a fairly hot codepath - no trace2_region please */
		/* NEEDSWORK: cache misses aren't recorded */
		bitmap = lazy_bitmap_for_commit(bitmap_git, commit);
		if (!bitmap)
			return NULL;
		return lookup_stored_bitmap(bitmap);
	}
	return lookup_stored_bitmap(kh_value(bitmap_git->bitmaps, hash_pos));
}

// Function: bitmap_free from ewah/bitmap.c (lines 304-311)
void bitmap_free(struct bitmap *bitmap)
{
	if (!bitmap)
		return;

	free(bitmap->words);
	free(bitmap);
}

// Function: bitmap_get from ewah/bitmap.c (lines 69-74)
int bitmap_get(struct bitmap *self, size_t pos)
{
	size_t block = EWAH_BLOCK(pos);
	return block < self->word_alloc &&
		(self->words[block] & EWAH_MASK(pos)) != 0;
}

// Function: bitmap_new from ewah/bitmap.c (lines 33-36)
struct bitmap *bitmap_new(void)
{
	return bitmap_word_alloc(32);
}

// Function: bitmap_or from ewah/bitmap.c (lines 132-139)
void bitmap_or(struct bitmap *self, const struct bitmap *other)
{
	size_t i;

	bitmap_grow(self, other->word_alloc);
	for (i = 0; i < other->word_alloc; i++)
		self->words[i] |= other->words[i];
}

// Function: bitmap_set from ewah/bitmap.c (lines 53-59)
void bitmap_set(struct bitmap *self, size_t pos)
{
	size_t block = EWAH_BLOCK(pos);

	bitmap_grow(self, block + 1);
	self->words[block] |= EWAH_MASK(pos);
}

// Function: fill_bitmap_tree from current file (lines 425-471)
static int fill_bitmap_tree(struct bitmap_writer *writer,
			    struct bitmap *bitmap,
			    struct tree *tree)
{
	int found;
	uint32_t pos;
	struct tree_desc desc;
	struct name_entry entry;

	/*
	 * If our bit is already set, then there is nothing to do. Both this
	 * tree and all of its children will be set.
	 */
	pos = find_object_pos(writer, &tree->object.oid, &found);
	if (!found)
		return -1;
	if (bitmap_get(bitmap, pos))
		return 0;
	bitmap_set(bitmap, pos);

	if (parse_tree(tree) < 0)
		die("unable to load tree object %s",
		    oid_to_hex(&tree->object.oid));
	init_tree_desc(&desc, &tree->object.oid, tree->buffer, tree->size);

	while (tree_entry(&desc, &entry)) {
		switch (object_type(entry.mode)) {
		case OBJ_TREE:
			if (fill_bitmap_tree(writer, bitmap,
					     lookup_tree(the_repository, &entry.oid)) < 0)
				return -1;
			break;
		case OBJ_BLOB:
			pos = find_object_pos(writer, &entry.oid, &found);
			if (!found)
				return -1;
			bitmap_set(bitmap, pos);
			break;
		default:
			/* Gitlink, etc; not reachable */
			break;
		}
	}

	free_tree_buffer(tree);
	return 0;
}

// Function: find_object_pos from current file (lines 198-214)
static uint32_t find_object_pos(struct bitmap_writer *writer,
				const struct object_id *oid, int *found)
{
	struct object_entry *entry = packlist_find(writer->to_pack, oid);

	if (!entry) {
		if (found)
			*found = 0;
		warning("Failed to write bitmap index. Packfile doesn't have full closure "
			"(object %s is missing)", oid_to_hex(oid));
		return 0;
	}

	if (found)
		*found = 1;
	return oe_in_pack_pos(writer->to_pack, entry);
}

// Function: prio_queue_get from prio-queue.c (lines 58-87)
void *prio_queue_get(struct prio_queue *queue)
{
	void *result;
	int ix, child;

	if (!queue->nr)
		return NULL;
	if (!queue->compare)
		return queue->array[--queue->nr].data; /* LIFO */

	result = queue->array[0].data;
	if (!--queue->nr)
		return result;

	queue->array[0] = queue->array[queue->nr];

	/* Push down the one at the root */
	for (ix = 0; ix * 2 + 1 < queue->nr; ix = child) {
		child = ix * 2 + 1; /* left */
		if (child + 1 < queue->nr &&
		    compare(queue, child, child + 1) >= 0)
			child++; /* use right child */

		if (compare(queue, ix, child) <= 0)
			break;

		swap(queue, child, ix);
	}
	return result;
}

// Function: prio_queue_put from prio-queue.c (lines 36-56)
void prio_queue_put(struct prio_queue *queue, void *thing)
{
	int ix, parent;

	/* Append at the end */
	ALLOC_GROW(queue->array, queue->nr + 1, queue->alloc);
	queue->array[queue->nr].ctr = queue->insertion_ctr++;
	queue->array[queue->nr].data = thing;
	queue->nr++;
	if (!queue->compare)
		return; /* LIFO */

	/* Bubble up the new one */
	for (ix = queue->nr - 1; ix; ix = parent) {
		parent = (ix - 1) / 2;
		if (compare(queue, parent, ix) <= 0)
			break;

		swap(queue, parent, ix);
	}
}

// Function: pseudo_merge_bitmap_for_commit from pack-bitmap.c (lines 1326-1355)
struct ewah_bitmap *pseudo_merge_bitmap_for_commit(struct bitmap_index *bitmap_git,
						   struct commit *commit)
{
	struct commit_list *p;
	struct bitmap *parents;
	struct pseudo_merge *match = NULL;

	if (!bitmap_git->pseudo_merges.nr)
		return NULL;

	parents = bitmap_new();

	for (p = commit->parents; p; p = p->next) {
		int pos = bitmap_position(bitmap_git, &p->item->object.oid);
		if (pos < 0 || pos >= bitmap_num_objects(bitmap_git))
			goto done;

		bitmap_set(parents, pos);
	}

	match = pseudo_merge_for_parents(&bitmap_git->pseudo_merges,
						parents);

done:
	bitmap_free(parents);
	if (match)
		return pseudo_merge_bitmap(&bitmap_git->pseudo_merges, match);

	return NULL;
}

// Function: rebuild_bitmap from pack-bitmap.c (lines 2757-2786)
int rebuild_bitmap(const uint32_t *reposition,
		   struct ewah_bitmap *source,
		   struct bitmap *dest)
{
	uint32_t pos = 0;
	struct ewah_iterator it;
	eword_t word;

	ewah_iterator_init(&it, source);

	while (ewah_iterator_next(&word, &it)) {
		uint32_t offset, bit_pos;

		for (offset = 0; offset < BITS_IN_EWORD; ++offset) {
			if ((word >> offset) == 0)
				break;

			offset += ewah_bit_ctz64(word >> offset);

			bit_pos = reposition[pos + offset];
			if (bit_pos > 0)
				bitmap_set(dest, bit_pos - 1);
			else /* can't reuse, we don't have the object */
				return -1;
		}

		pos += BITS_IN_EWORD;
	}
	return 0;
}

// Function: repo_get_commit_tree from commit.c (lines 420-430)
struct tree *repo_get_commit_tree(struct repository *r,
				  const struct commit *commit)
{
	if (commit->maybe_tree || !commit->object.parsed)
		return commit->maybe_tree;

	if (commit_graph_position(commit) != COMMIT_NOT_FROM_GRAPH)
		return get_commit_tree_in_graph(r, commit);

	return NULL;
}
        ```

        DEFECT HYPOTHESIS
        A real defect exists if `prio_queue_get(queue)` can still return NULL on a path that reaches the later uses of `c`.

        Structured Verification:
        Defect Premise: The risky path requires `queue->nr == 0` at the call even though the loop body was entered.
Counter-Evidence: The loop condition is checked immediately before the call and the slice offers no visible mutation that empties the queue before `prio_queue_get(queue)`.

        Defect Hypothesis Status: REFUTED

        SAFETY HYPOTHESIS
        The warning is a false positive if the loop invariant `while (queue->nr)` makes the queue non-empty whenever `prio_queue_get(queue)` is called.

        Structured Verification:
        Guard / Constraint: `while (queue->nr)` is the visible queue-nonempty guard.
Path Feasibility: Inside this loop body, the call to `prio_queue_get(queue)` is reached only after the non-empty condition has been satisfied.
Reachability: The later uses of `c` occur in the same iteration that began under the non-empty invariant.

        Safety Hypothesis Status: SUPPORTED

        WARNING-EVOLUTION EVIDENCE ASSESSMENT
        Structured Warning-Evolution Evidence:
- matched: no
- matching method: Unavailable
- matched version: Unavailable
- matched child warning: Unavailable
- location threshold: 3
- later versions checked: Unavailable
- SCA reports checked: Unavailable
- original evolution state: Unavailable
- trace completeness: Unavailable
- evidence reliability: LOW

        Evolution Analysis:
        The heuristic-side disagreement only tells us that the warning deserves re-checking. The preserved evolution artifact is weak and does not establish a current defect path, so the same-slice loop invariant remains the decisive evidence.

        CROSS-EVIDENCE RESOLUTION
        The safety explanation is stronger because the visible queue invariant directly blocks the null-return premise that the defect hypothesis needs. Historical disagreement does not create a defect path by itself.

        Final Label: FP

## Shot 4

Tool: codeql
        Rule: cpp/unbounded-write
        CWE: CWE-787
        Function: <global>
        Warning Message: This 'call to strcpy' with input from [a command-line argument](1) may overflow the destination.

        Stage1 Semantic Prediction: TP
        Stage1 Semantic Confidence: High
        Stage1 Supporting Reasoning:
        The code uses strcpy to copy argv[n] into a buffer of size PATH_MAX without checking the length of argv[n]. Since argv[n] is a command-line argument, its length is uncontrolled and can exceed PATH_MAX, causing a buffer overflow. The allocation is fixed at PATH_MAX, and there is no length check before the copy. The CWE knowledge confirms that unbounded copy from a source without size validation is a classic buffer overflow. The code path is reachable for any argv[n] that is a directory, and the overflow is feasible.

        CWE Reasoning Schema: CWE-787

        Code Context:
        ```c
        // ========== Sliced Code ==========

int main(int argc, char **argv) {
    FuzzerInitialize(&argc, &argv);
    for (n = 1; n < argc; ++n) {
        size_t dirname_len = strlen(argv[n]);
        const char *filename = NULL;
        char *pathname = NULL;
        OPENSSL_DIR_CTX *ctx = NULL;
        int wasdir = 0;
        while ((filename = OPENSSL_DIR_read(&ctx, argv[n])) != NULL) {
            wasdir = 1;
            if (pathname == NULL) {
                pathname = malloc(PATH_MAX);
                if (pathname == NULL)
                    break;
                strcpy(pathname, argv[n]);  // The line where the warning is located
#ifdef __VMS
                if (strchr(":<]", pathname[dirname_len - 1]) == NULL)
#endif
                    pathname[dirname_len++] = '/';
                pathname[dirname_len] = '\0';
            }
            strcpy(pathname + dirname_len, filename);
            testfile(pathname);
        }
        OPENSSL_DIR_end(&ctx);
        if (!wasdir)
            testfile(argv[n]);
        free(pathname);
    }
}


// ========== Called Function Definitions ==========

// Function: FuzzerInitialize from fuzz/acert.c (lines 17-23)
int FuzzerInitialize(int *argc, char ***argv)
{
    OPENSSL_init_crypto(OPENSSL_INIT_LOAD_CRYPTO_STRINGS, NULL);
    ERR_clear_error();
    CRYPTO_free_ex_index(0, -1);
    return 1;
}

// Function: OPENSSL_DIR_end from include/internal/o_dir.h (lines 51-51)
int OPENSSL_DIR_end(OPENSSL_DIR_CTX **ctx);

// Function: OPENSSL_DIR_read from include/internal/o_dir.h (lines 49-49)
const char *OPENSSL_DIR_read(OPENSSL_DIR_CTX **ctx, const char *directory);

// Function: testfile from current file (lines 37-59)
static void testfile(const char *pathname)
{
    struct stat st;
    FILE *f;
    unsigned char *buf;
    size_t s;

    if (stat(pathname, &st) < 0 || !S_ISREG(st.st_mode))
        return;
    printf("# %s\n", pathname);
    fflush(stdout);
    f = fopen(pathname, "rb");
    if (f == NULL)
        return;
    buf = malloc(st.st_size);
    if (buf != NULL) {
        s = fread(buf, 1, st.st_size, f);
        OPENSSL_assert(s == (size_t)st.st_size);
        FuzzerTestOneInput(buf, s);
        free(buf);
    }
    fclose(f);
}
        ```

        DEFECT HYPOTHESIS
        A real overflow exists if the program copies `argv[n]` into a fixed `PATH_MAX` buffer without any visible bound on the source length.

        Structured Verification:
        Write Operation: `strcpy(pathname, argv[n])` copies the whole argument.
Destination Capacity: `pathname = malloc(PATH_MAX)` fixes the buffer size.
Length Relation: `dirname_len = strlen(argv[n])` is observed, but there is no visible check comparing it with `PATH_MAX`.
Reachability: The copy executes on the feasible path where the directory read begins and `pathname` is first allocated.

        Defect Hypothesis Status: SUPPORTED

        SAFETY HYPOTHESIS
        The warning is a false positive if the visible code bounds `argv[n]` or otherwise ensures that the copied string cannot exceed the destination capacity.

        Structured Verification:
        The visible code does not provide a range check, truncation, or guard that constrains the length of `argv[n]` before the copy. The safety hypothesis therefore lacks semantic support in the current slice.

        Safety Hypothesis Status: REFUTED

        WARNING-EVOLUTION EVIDENCE ASSESSMENT
        Structured Warning-Evolution Evidence:
- matched: yes
- matching method: Location-based match
- matched version: 3.6.0
- matched child warning: {'file_path': 'fuzz/test-corpus.c', 'rule_id': 'cpp/toctou-race-condition', 'cwe': 'CWE-367', 'function_name': 'testfile'}
- location threshold: 3
- later versions checked: Unavailable
- SCA reports checked: Unavailable
- original evolution state: Unavailable
- trace completeness: Unavailable
- evidence reliability: HIGH

        Evolution Analysis:
        The later-version correspondence records historical persistence, but it cannot supply a missing source-length guard. The current semantic capacity analysis remains stronger than the historical warning observation.

        CROSS-EVIDENCE RESOLUTION
        The defect hypothesis is supported by a concrete same-slice overflow path: an uncontrolled argument is copied into a fixed-size buffer with no visible bound check. The historical correspondence does not neutralize that capacity mismatch.

        Final Label: TP

## Shot 5

Tool: codeql
        Rule: cpp/invalid-pointer-deref
        CWE: CWE-787
        Function: <global>
        Warning Message: This write might be out of bounds, as the pointer might be equal to [call to xmallocz](1) + [... ++](2).

        Stage1 Semantic Prediction: TP
        Stage1 Semantic Confidence: High
        Stage1 Supporting Reasoning:
        The code allocates 'buf' with xmallocz(size), which allocates size+1 bytes (including a null terminator). Then it reads exactly 'size' bytes into buf. After the read, it writes a newline at buf[size], which is the last byte of the allocated buffer (since xmallocz allocated size+1 bytes). However, the code then increments size (buf[size++] = '\n'), making size = original_size + 1. Later, the code uses 'size' in hash_object_file and add_patterns_from_buffer, which may read beyond the allocated buffer. Specifically, hash_object_file is called with 'size' as the length, which is now one more than the allocated buffer size, leading to an out-of-bounds read. Additionally, add_patterns_from_buffer iterates up to 'size' and accesses buf[i], which can read one byte past the allocated buffer. This is a classic off-by-one error: the newline write is safe, but the subsequent use of the incremented size causes out-of-bounds reads.

        CWE Reasoning Schema: CWE-787

        Code Context:
        ```c
        // ========== Sliced Code ==========

static int add_patterns(const char *fname, const char *base, int baselen,
			struct pattern_list *pl, struct index_state *istate,
			unsigned flags, struct oid_stat *oid_stat)
{
	if (flags & PATTERN_NOFOLLOW)
		fd = open_nofollow(fname, O_RDONLY);
	else
		fd = open(fname, O_RDONLY);
		size = xsize_t(st.st_size);
		if (size == 0) {
			if (oid_stat) {
				fill_stat_data(&oid_stat->stat, &st);
				oidcpy(&oid_stat->oid, the_hash_algo->empty_blob);
				oid_stat->valid = 1;
			}
			close(fd);
			return 0;
		}
		buf = xmallocz(size);
		if (read_in_full(fd, buf, size) != size) {
			free(buf);
			close(fd);
			return -1;
		}
		buf[size++] = '\n';  // The line where the warning is located
		close(fd);
		if (oid_stat) {
			int pos;
			if (oid_stat->valid &&
			    !match_stat_data_racy(istate, &oid_stat->stat, &st))
				; /* no content change, oid_stat->oid still good */
			else if (istate &&
				 (pos = index_name_pos(istate, fname, strlen(fname))) >= 0 &&
				 !ce_stage(istate->cache[pos]) &&
				 ce_uptodate(istate->cache[pos]) &&
				 !would_convert_to_git(istate, fname))
				oidcpy(&oid_stat->oid,
				       &istate->cache[pos]->oid);
			else
				hash_object_file(the_hash_algo, buf, size,
						 OBJ_BLOB, &oid_stat->oid);
			fill_stat_data(&oid_stat->stat, &st);
			oid_stat->valid = 1;
		}
	}
	if (size > PATTERN_MAX_FILE_SIZE) {
		warning("ignoring excessively large pattern file: %s", fname);
		free(buf);
		return -1;
	}
	add_patterns_from_buffer(buf, size, base, baselen, pl);
	free(buf);
	return 0;
}


// ========== Called Function Definitions ==========

// Function: add_patterns_from_buffer from current file (lines 1184-1212)
static int add_patterns_from_buffer(char *buf, size_t size,
				    const char *base, int baselen,
				    struct pattern_list *pl)
{
	char *orig = buf;
	int i, lineno = 1;
	char *entry;

	hashmap_init(&pl->recursive_hashmap, pl_hashmap_cmp, NULL, 0);
	hashmap_init(&pl->parent_hashmap, pl_hashmap_cmp, NULL, 0);

	if (skip_utf8_bom(&buf, size))
		size -= buf - orig;

	entry = buf;

	for (i = 0; i < size; i++) {
		if (buf[i] == '\n') {
			if (entry != buf + i && entry[0] != '#') {
				buf[i - (i && buf[i-1] == '\r')] = 0;
				trim_trailing_spaces(entry);
				add_pattern(entry, base, baselen, pl, lineno);
			}
			lineno++;
			entry = buf + i + 1;
		}
	}
	return 0;
}

// Macro: ce_stage from read-cache-ll.h (line 120)
#define ce_stage(ce) ((CE_STAGEMASK & (ce)->ce_flags) >> CE_STAGESHIFT)

// Macro: ce_uptodate from read-cache-ll.h (line 121)
#define ce_uptodate(ce) ((ce)->ce_flags & CE_UPTODATE)

// Function: fill_stat_data from statinfo.c (lines 23-34)
void fill_stat_data(struct stat_data *sd, struct stat *st)
{
	sd->sd_ctime.sec = (unsigned int)st->st_ctime;
	sd->sd_mtime.sec = (unsigned int)st->st_mtime;
	sd->sd_ctime.nsec = ST_CTIME_NSEC(*st);
	sd->sd_mtime.nsec = ST_MTIME_NSEC(*st);
	sd->sd_dev = st->st_dev;
	sd->sd_ino = st->st_ino;
	sd->sd_uid = st->st_uid;
	sd->sd_gid = st->st_gid;
	sd->sd_size = munge_st_size(st->st_size);
}

// Function: hash_object_file from object-file.c (lines 2098-2103)
void hash_object_file(const struct git_hash_algo *algo, const void *buf,
		      unsigned long len, enum object_type type,
		      struct object_id *oid)
{
	hash_object_file_literally(algo, buf, len, type_name(type), oid);
}

// Function: index_name_pos from read-cache.c (lines 553-556)
int index_name_pos(struct index_state *istate, const char *name, int namelen)
{
	return index_name_stage_pos(istate, name, namelen, 0, EXPAND_SPARSE);
}

// Function: match_stat_data_racy from read-cache.c (lines 373-379)
int match_stat_data_racy(const struct index_state *istate,
			 const struct stat_data *sd, struct stat *st)
{
	if (is_racy_stat(istate, sd))
		return MTIME_CHANGED;
	return match_stat_data(sd, st);
}

// Function: oidcpy from hash.h (lines 371-375)
static inline void oidcpy(struct object_id *dst, const struct object_id *src)
{
	memcpy(dst->hash, src->hash, GIT_MAX_RAWSZ);
	dst->algo = src->algo;
}

// Function: open_nofollow from wrapper.c (lines 734-748)
int open_nofollow(const char *path, int flags)
{
#ifdef O_NOFOLLOW
	return open(path, flags | O_NOFOLLOW);
#else
	struct stat st;
	if (lstat(path, &st) < 0)
		return -1;
	if (S_ISLNK(st.st_mode)) {
		errno = ELOOP;
		return -1;
	}
	return open(path, flags);
#endif
}

// Function: read_in_full from wrapper.c (lines 283-300)
ssize_t read_in_full(int fd, void *buf, size_t count)
{
	char *p = buf;
	ssize_t total = 0;

	while (count > 0) {
		ssize_t loaded = xread(fd, p, count);
		if (loaded < 0)
			return -1;
		if (loaded == 0)
			return total;
		count -= loaded;
		p += loaded;
		total += loaded;
	}

	return total;
}

// Function: warning from usage.c (lines 285-292)
void warning(const char *warn, ...)
{
	va_list params;

	va_start(params, warn);
	warn_routine(warn, params);
	va_end(params);
}

// Function: would_convert_to_git from convert.h (lines 139-143)
static inline int would_convert_to_git(struct index_state *istate,
				       const char *path)
{
	return convert_to_git(istate, path, NULL, 0, NULL, 0);
}

// Function: xmallocz from wrapper.c (lines 92-95)
void *xmallocz(size_t size)
{
	return do_xmallocz(size, 0);
}

// Function: xsize_t from git-compat-util.h (lines 1279-1284)
static inline size_t xsize_t(off_t len)
{
	if (len < 0 || (uintmax_t) len > SIZE_MAX)
		die("Cannot handle files this big");
	return (size_t) len;
}
        ```

        DEFECT HYPOTHESIS
        A real bounds defect exists if `buf[size++] = '\n'` and the later uses of `size` make the code read or write past the valid extent of the allocation.

        Structured Verification:
        Defect Premise: Stage1 treats the incremented `size` as exceeding the valid allocation.
Counter-Evidence: The slice shows `xmallocz(size)` rather than `xmalloc(size)`, which is the exact capacity fact that must be reconciled with the later `size` use.

        Defect Hypothesis Status: REFUTED

        SAFETY HYPOTHESIS
        The warning is a false positive if `xmallocz(size)` already reserves the extra byte needed for the terminator/newline and the visible subsequent operations stay within that extended allocation.

        Structured Verification:
        Capacity Predicate: `xmallocz(size)` reserves `size + 1` bytes.
Bounds Relation: Writing at `buf[size]` uses that extra byte, and the updated `size` then includes the added newline that is still inside the extended allocation.
Reachability: The later hashing and buffer-processing calls consume the now-terminated buffer rather than stepping beyond the allocated space.

        Safety Hypothesis Status: SUPPORTED

        WARNING-EVOLUTION EVIDENCE ASSESSMENT
        Structured Warning-Evolution Evidence:
- matched: yes
- matching method: Location-based match
- matched version: 2.49.0
- matched child warning: {'file_path': 'dir.c', 'rule_id': 'cpp/declaration-hides-variable', 'function_name': 'write_one_dir'}
- location threshold: 3
- later versions checked: Unavailable
- SCA reports checked: Unavailable
- original evolution state: Unavailable
- trace completeness: Unavailable
- evidence reliability: HIGH

        Evolution Analysis:
        The persisted later-version correspondence is only historical warning evidence. The decisive issue is the visible allocation arithmetic, which resolves the competing hypotheses in favor of safety.

        CROSS-EVIDENCE RESOLUTION
        The warning-looking write becomes safe once the extra byte from `xmallocz(size)` is accounted for. Because the safety hypothesis has direct same-slice support, the defect hypothesis is not the better explanation.

        Final Label: FP

## Shot 6

Tool: codeql
        Rule: cpp/unbounded-write
        CWE: CWE-787
        Function: maketitle
        Warning Message: This 'call to strcpy' with input from [an environment variable](1) may overflow the destination.
This 'call to strcpy' with input from [an environment variable](2) may overflow the destination.
This 'call to strcpy' with input from [an environment variable](3) may overflow the destination.
This 'call to strcpy' with input from [an environment variable](4) may overflow the destination.
This 'call to strcpy' with input from [an environment variable](5) may overflow the destination.
This 'call to strcpy' with input from [an environment variable](6) may overflow the destination.
This 'call to strcpy' with input from [buffer read by read](7) may overflow the destination.
This 'call to strcpy' with input from [string read by fgets](8) may overflow the destination.
This 'call to strcpy' with input from [string read by fread](9) may overflow the destination.
This 'call to strcpy' with input from [string read by fgets](10) may overflow the destination.
This 'call to strcpy' with input from [string read by fgets](11) may overflow the destination.
This 'call to strcpy' with input from [buffer read by read](12) may overflow the destination.
This 'call to strcpy' with input from [string read by fread](13) may overflow the destination.
This 'call to strcpy' with input from [string read by fread](14) may overflow the destination.
This 'call to strcpy' with input from [external](15) may overflow the destination.
This 'call to strcpy' with input from [external](16) may overflow the destination.
This 'call to strcpy' with input from [external](17) may overflow the destination.
This 'call to strcpy' with input from [external](18) may overflow the destination.
This 'call to strcpy' with input from [external](19) may overflow the destination.
This 'call to strcpy' with input from [external](20) may overflow the destination.

        Stage1 Semantic Prediction: FP
        Stage1 Semantic Confidence: High
        Stage1 Supporting Reasoning:
        The destination buffer 'buf' has size IOSIZE (likely 1024 bytes). The source 'name' is derived from 'curbuf->b_ffname' via 'gettail', which returns a pointer into the file name. The file name length is bounded by the filesystem (typically PATH_MAX, e.g., 4096 bytes on Linux, but Vim's internal limits are smaller). However, before the STRCPY, the code truncates 'name' by advancing it by 'namelen' if 'namelen > 100', ensuring the copied portion is at most 100 bytes. Additionally, the destination 'buf' is at least 1024 bytes, so copying at most 100 bytes cannot overflow. The warning is a false positive because the source is effectively bounded to a safe length.

        CWE Reasoning Schema: CWE-787

        Code Context:
        ```c
        // ========== Sliced Code ==========

static char_u *lasttitle = NULL;
static char_u *lasticon = NULL;
    void
maketitle(void)
{
    char_u	buf[IOSIZE];
    if (!p_title && !p_icon && lasttitle == NULL && lasticon == NULL)
	return;  // nothing to do
    if (p_title)
    {
	int maxlen = 0;
	if (p_titlelen > 0)
	{
	    maxlen = p_titlelen * Columns / 100;
	    if (maxlen < 10)
		maxlen = 10;
	}
	title_str = buf;
	else
	{
	    if (curbuf->b_fname == NULL)
		buflen = vim_snprintf_safelen((char *)buf,
		    SPACE_FOR_FNAME, "%s", _("[No Name]"));
		buflen = vim_snprintf_safelen((char *)buf,
		    SPACE_FOR_FNAME, "%s",
		    ((p = transstr(gettail(curbuf->b_fname))) != NULL)
	    }
#ifdef FEAT_TERMINAL
	    if (curbuf->b_term == NULL)
#endif
	    {
		switch (bufIsChanged(curbuf)
			+ (curbuf->b_p_ro * 2)
			+ (!curbuf->b_p_ma * 4))
		{
		    case 1:
			buflen += vim_snprintf_safelen(
			    (char *)buf + buflen,
			    sizeof(buf) - buflen, " +");
			break;
		    case 2:
			buflen += vim_snprintf_safelen(
			    (char *)buf + buflen,
			    sizeof(buf) - buflen, " =");
			break;
		    case 3:
			buflen += vim_snprintf_safelen(
			    (char *)buf + buflen,
			    sizeof(buf) - buflen, " =+");
			break;
		    case 6:
			buflen += vim_snprintf_safelen(
			    (char *)buf + buflen,
			    sizeof(buf) - buflen, " -");
			break;
		    case 7:
			buflen += vim_snprintf_safelen(
			    (char *)buf + buflen,
			    sizeof(buf) - buflen, " -+");
			break;
		}
	    }
	    if (curbuf->b_fname != NULL
#ifdef FEAT_TERMINAL
		    && curbuf->b_term == NULL
#endif
		    )
	    {
		buflen += vim_snprintf_safelen((char *)buf + buflen,
		    sizeof(buf) - buflen, " (");
		home_replace(curbuf, curbuf->b_ffname,
		    buf + buflen, (int)(SPACE_FOR_DIR - buflen), TRUE);
		p = gettail_sep(buf + buflen);
		if (p == buf + buflen)
		{
		    buflen += vim_snprintf_safelen((char *)buf + buflen,
			SPACE_FOR_DIR - buflen, "%s)", _("help"));
		}
		else
		{
		    if (buflen < SPACE_FOR_DIR)
		    {
			buflen += vim_snprintf_safelen((char *)buf + buflen,
			    SPACE_FOR_DIR - buflen, "%s)",
			    ((p = transstr(buf + buflen)) != NULL)
		    }
		    else
			buflen += vim_snprintf_safelen((char *)buf + buflen,
			    SPACE_FOR_ARGNR - buflen, "...)");
		}
	    }
	    buflen += append_arg_number(curwin, buf + buflen,
		SPACE_FOR_ARGNR - buflen, FALSE);
	    buflen += vim_snprintf_safelen((char *)buf + buflen,
		sizeof(buf) - buflen, " - %s",
	    if (maxlen > 0)
	    {
		if (vim_strsize(buf) > maxlen)
		    trunc_string(buf, buf, maxlen, sizeof(buf));
	    }
	}
    }
    if (p_icon)
	icon_str = buf;
	if (*p_iconstring != NUL)
	    name = buf_spname(curbuf);
	    if (name == NULL)
		name = gettail(curbuf->b_ffname);
	    namelen = (int)STRLEN(name);
	    if (namelen > 100)
		namelen -= 100;
		if (has_mbyte)
		    namelen += (*mb_tail_off)(name, name + namelen) + 1;
		name += namelen;
	    STRCPY(buf, name);  // The line where the warning is located
	    trans_characters(buf, sizeof(buf));


// ========== Called Function Definitions ==========

// Macro: STRCPY from src/vim.h (line 1780)
#define STRCPY(d, s)	    strcpy((char *)(d), (char *)(s))

// Macro: STRLEN from src/vim.h (line 1779)
#define STRLEN(s)	    strlen((char *)(s))

// Macro: _ from src/GvimExt/gvimext.cpp (line 182)
# define _(x)	    x

// Function: append_arg_number from current file (lines 5428-5449)
static int
append_arg_number(
    win_T	*wp,
    char_u	*buf,
    size_t	buflen,
    int		add_file)	// Add "file" before the arg number
{
    if (ARGCOUNT <= 1)		// nothing to do
	return 0;

    char *msg;
    switch ((wp->w_arg_idx_invalid ? 1 : 0) + (add_file ? 2 : 0))
    {
	case 0: msg = _(" (%d of %d)"); break;
	case 1: msg = _(" ((%d) of %d)"); break;
	case 2: msg = _(" (file %d of %d)"); break;
	case 3: msg = _(" (file (%d) of %d)"); break;
    }

    return (int)vim_snprintf_safelen((char *)buf, buflen, msg,
						  wp->w_arg_idx + 1, ARGCOUNT);
}

// Function: bufIsChanged from src/undo.c (lines 3604-3612)
int
bufIsChanged(buf_T *buf)
{
#ifdef FEAT_TERMINAL
    if (term_job_running_not_none(buf->b_term))
	return TRUE;
#endif
    return bufIsChangedNotTerm(buf);
}

// Function: buf_spname from current file (lines 6069-6112)
char_u *
buf_spname(buf_T *buf)
{
#if defined(FEAT_QUICKFIX)
    if (bt_quickfix(buf))
    {
	/*
	 * Differentiate between the quickfix and location list buffers using
	 * the buffer number stored in the global quickfix stack.
	 */
	if (buf->b_fnum == qf_stack_get_bufnr())
	    return (char_u *)_(msg_qflist);
	else
	    return (char_u *)_(msg_loclist);
    }
#endif

    // There is no _file_ when 'buftype' is "nofile", b_sfname
    // contains the name as specified by the user.
    if (bt_nofilename(buf))
    {
#ifdef FEAT_TERMINAL
	if (buf->b_term != NULL)
	    return term_get_status_text(buf->b_term);
#endif
	if (buf->b_fname != NULL)
	    return buf->b_fname;
	if (buf == cmdwin_buf)
	    return (char_u *)_("[Command Line]");
#ifdef FEAT_JOB_CHANNEL
	if (bt_prompt(buf))
	    return (char_u *)_("[Prompt]");
#endif
#ifdef FEAT_PROP_POPUP
	if (bt_popup(buf))
	    return (char_u *)_("[Popup]");
#endif
	return (char_u *)_("[Scratch]");
    }

    if (buf->b_fname == NULL)
	return buf_get_fname(buf);
    return NULL;
}

// Function: gettail from src/filepath.c (lines 2930-2944)
char_u *
gettail(char_u *fname)
{
    char_u  *p1, *p2;

    if (fname == NULL)
	return (char_u *)"";
    for (p1 = p2 = get_past_head(fname); *p2; )	// find last part of path
    {
	if (vim_ispathsep_nocolon(*p2))
	    p1 = p2 + 1;
	MB_PTR_ADV(p2);
    }
    return p1;
}

// Function: gettail_sep from src/filepath.c (lines 2951-2966)
char_u *
gettail_sep(char_u *fname)
{
    char_u	*p;
    char_u	*t;

    p = get_past_head(fname);	// don't remove the '/' from "c:/file"
    t = gettail(fname);
    while (t > p && after_pathsep(fname, t))
	--t;
#ifdef VMS
    // path separator is part of the path
    ++t;
#endif
    return t;
}

// Function: home_replace from src/filepath.c (lines 2695-2813)
void
home_replace(
    buf_T	*buf,	// when not NULL, check for help files
    char_u	*src,	// input file name
    char_u	*dst,	// where to put the result
    int		dstlen,	// maximum length of the result
    int		one)	// if TRUE, only replace one file name, include
			// spaces and commas in the file name.
{
    size_t	dirlen = 0, envlen = 0;
    size_t	len;
    char_u	*homedir_env, *homedir_env_orig;
    char_u	*p;

    if (src == NULL)
    {
	*dst = NUL;
	return;
    }

    /*
     * If the file is a help file, remove the path completely.
     */
    if (buf != NULL && buf->b_help)
    {
	vim_snprintf((char *)dst, dstlen, "%s", gettail(src));
	return;
    }

    /*
     * We check both the value of the $HOME environment variable and the
     * "real" home directory.
     */
    if (homedir != NULL)
	dirlen = STRLEN(homedir);

#ifdef VMS
    homedir_env_orig = homedir_env = mch_getenv((char_u *)"SYS$LOGIN");
#else
    homedir_env_orig = homedir_env = mch_getenv((char_u *)"HOME");
#endif
#ifdef MSWIN
    if (homedir_env == NULL)
	homedir_env_orig = homedir_env = mch_getenv((char_u *)"USERPROFILE");
#endif
    // Empty is the same as not set.
    if (homedir_env != NULL && *homedir_env == NUL)
	homedir_env = NULL;

    if (homedir_env != NULL && *homedir_env == '~')
    {
	size_t	usedlen = 0;
	size_t	flen;
	char_u	*fbuf = NULL;

	flen = STRLEN(homedir_env);
	(void)modify_fname((char_u *)":p", FALSE, &usedlen,
						  &homedir_env, &fbuf, &flen);
	flen = STRLEN(homedir_env);
	if (flen > 0 && vim_ispathsep(homedir_env[flen - 1]))
	    // Remove the trailing / that is added to a directory.
	    homedir_env[flen - 1] = NUL;
    }

    if (homedir_env != NULL)
	envlen = STRLEN(homedir_env);

    if (!one)
	src = skipwhite(src);
    while (*src && dstlen > 0)
    {
	/*
	 * Here we are at the beginning of a file name.
	 * First, check to see if the beginning of the file name matches
	 * $HOME or the "real" home directory. Check that there is a '/'
	 * after the match (so that if e.g. the file is "/home/pieter/bla",
	 * and the home directory is "/home/piet", the file does not end up
	 * as "~er/bla" (which would seem to indicate the file "bla" in user
	 * er's home directory)).
	 */
	p = homedir;
	len = dirlen;
	for (;;)
	{
	    if (   len
		&& fnamencmp(src, p, len) == 0
		&& (vim_ispathsep(src[len])
		    || (!one && (src[len] == ',' || src[len] == ' '))
		    || src[len] == NUL))
	    {
		src += len;
		if (--dstlen > 0)
		    *dst++ = '~';

		// Do not add directory separator into dst, because dst is
		// expected to just return the directory name without the
		// directory separator '/'.
		break;
	    }
	    if (p == homedir_env)
		break;
	    p = homedir_env;
	    len = envlen;
	}

	// if (!one) skip to separator: space or comma
	while (*src && (one || (*src != ',' && *src != ' ')) && --dstlen > 0)
	    *dst++ = *src++;
	// skip separator
	while ((*src == ' ' || *src == ',') && --dstlen > 0)
	    *dst++ = *src++;
    }
    // if (dstlen == 0) out of space, what to do???

    *dst = NUL;

    if (homedir_env != homedir_env_orig)
	vim_free(homedir_env);
}

// Function: trans_characters from src/charset.c (lines 302-335)
void
trans_characters(
    char_u	*buf,
    int		bufsize)
{
    int		len;		// length of string needing translation
    int		room;		// room in buffer after string
    char_u	*trs;		// translated character
    int		trs_len;	// length of trs[]

    len = (int)STRLEN(buf);
    room = bufsize - len;
    while (*buf != 0)
    {
	// Assume a multi-byte character doesn't need translation.
	if (has_mbyte && (trs_len = (*mb_ptr2len)(buf)) > 1)
	    len -= trs_len;
	else
	{
	    trs = transchar_byte(*buf);
	    trs_len = (int)STRLEN(trs);
	    if (trs_len > 1)
	    {
		room -= trs_len - 1;
		if (room <= 0)
		    return;
		mch_memmove(buf + trs_len, buf + 1, (size_t)len);
	    }
	    mch_memmove(buf, trs, (size_t)trs_len);
	    --len;
	}
	buf += trs_len;
    }
}

// Function: transstr from src/charset.c (lines 341-403)
char_u *
transstr(char_u *s)
{
    char_u	*res;
    char_u	*p;
    int		l, len, c;
    char_u	hexbuf[11];

    if (has_mbyte)
    {
	// Compute the length of the result, taking account of unprintable
	// multi-byte characters.
	len = 0;
	p = s;
	while (*p != NUL)
	{
	    if ((l = (*mb_ptr2len)(p)) > 1)
	    {
		c = (*mb_ptr2char)(p);
		p += l;
		if (vim_isprintc(c))
		    len += l;
		else
		{
		    transchar_hex(hexbuf, c);
		    len += (int)STRLEN(hexbuf);
		}
	    }
	    else
	    {
		l = byte2cells(*p++);
		if (l > 0)
		    len += l;
		else
		    len += 4;	// illegal byte sequence
	    }
	}
	res = alloc(len + 1);
    }
    else
	res = alloc(vim_strsize(s) + 1);

    if (res == NULL)
	return NULL;

    *res = NUL;
    p = s;
    while (*p != NUL)
    {
	if (has_mbyte && (l = (*mb_ptr2len)(p)) > 1)
	{
	    c = (*mb_ptr2char)(p);
	    if (vim_isprintc(c))
		STRNCAT(res, p, l);	// append printable multi-byte char
	    else
		transchar_hex(res + STRLEN(res), c);
	    p += l;
	}
	else
	    STRCAT(res, transchar_byte(*p++));
    }
    return res;
}

// Function: trunc_string from src/message.c (lines 258-374)
void
trunc_string(
    char_u	*s,
    char_u	*buf,
    int		room_in,
    int		buflen)
{
    size_t	room = room_in - 3; // "..." takes 3 chars
    size_t	half;
    size_t	len = 0;
    int		e;
    int		i;
    int		n;

    if (*s == NUL)
    {
	if (buflen > 0)
	    *buf = NUL;
	return;
    }

    if (room_in < 3)
	room = 0;
    half = room / 2;

    // First part: Start of the string.
    for (e = 0; len < half && e < buflen; ++e)
    {
	if (s[e] == NUL)
	{
	    // text fits without truncating!
	    buf[e] = NUL;
	    return;
	}
	n = ptr2cells(s + e);
	if (len + n > half)
	    break;
	len += n;
	buf[e] = s[e];
	if (has_mbyte)
	    for (n = (*mb_ptr2len)(s + e); --n > 0; )
	    {
		if (++e == buflen)
		    break;
		buf[e] = s[e];
	    }
    }

    // Last part: End of the string.
    i = e;
    if (enc_dbcs != 0)
    {
	// For DBCS going backwards in a string is slow, but
	// computing the cell width isn't too slow: go forward
	// until the rest fits.
	n = vim_strsize(s + i);
	while (len + n > room)
	{
	    n -= ptr2cells(s + i);
	    i += (*mb_ptr2len)(s + i);
	}
    }
    else if (enc_utf8)
    {
	// For UTF-8 we can go backwards easily.
	half = i = (int)STRLEN(s);
	for (;;)
	{
	    do
		half = half - utf_head_off(s, s + half - 1) - 1;
	    while (half > 0 && utf_iscomposing(utf_ptr2char(s + half)));
	    n = ptr2cells(s + half);
	    if (len + n > room || half == 0)
		break;
	    len += n;
	    i = (int)half;
	}
    }
    else
    {
	for (i = (int)STRLEN(s);
		   i - 1 >= 0 && len + (n = ptr2cells(s + i - 1)) <= room; --i)
	    len += n;
    }


    if (i <= e + 3)
    {
	// text fits without truncating
	if (s != buf)
	{
	    len = STRLEN(s);
	    if (len >= (size_t)buflen)
		len = buflen - 1;
	    len = len - e + 1;
	    if (len < 1)
		buf[e - 1] = NUL;
	    else
		mch_memmove(buf + e, s + e, len);
	}
    }
    else if (e + 3 < buflen)
    {
	// set the middle and copy the last part
	mch_memmove(buf + e, "...", (size_t)3);
	len = STRLEN(s + i) + 1;
	if (len >= (size_t)buflen - e - 3)
	    len = buflen - e - 3 - 1;
	mch_memmove(buf + e + 3, s + i, len);
	buf[e + 3 + len - 1] = NUL;
    }
    else
    {
	// can't fit in the "...", just truncate it
	buf[buflen - 1] = NUL;
    }
}

// Function: vim_snprintf_safelen from src/strings.c (lines 2499-2515)
size_t
vim_snprintf_safelen(char *str, size_t str_m, const char *fmt, ...)
{
    va_list ap;
    int	    str_l;

    va_start(ap, fmt);
    str_l = vim_vsnprintf(str, str_m, fmt, ap);
    va_end(ap);

    if (str_l < 0)
    {
	*str = NUL;
	return 0;
    }
    return ((size_t)str_l >= str_m) ? str_m - 1 : (size_t)str_l;
}

// Function: vim_strsize from src/charset.c (lines 716-720)
int
vim_strsize(char_u *s)
{
    return vim_strnsize(s, (int)MAXCOL);
}
        ```

        DEFECT HYPOTHESIS
        A real overflow exists if the final `STRCPY(buf, name)` can still copy an uncontrolled tail string larger than `buf[IOSIZE]`.

        Structured Verification:
        Defect Premise: The danger story needs `name` to remain effectively unbounded at the copy site.
Counter-Evidence: The visible code computes `namelen`, subtracts 100 if necessary, adjusts for multibyte tails, and advances `name` before the copy.

        Defect Hypothesis Status: REFUTED

        SAFETY HYPOTHESIS
        The warning is a false positive if the visible truncation logic ensures that only a bounded suffix of `name` reaches the destination copy.

        Structured Verification:
        Bounds Guard: `if (namelen > 100) namelen -= 100; ... name += namelen;` keeps only the trailing bounded portion.
Destination Capacity: `buf` has static size `IOSIZE`, much larger than the retained suffix.
Reachability: The same visible branch performs the truncation immediately before `STRCPY(buf, name)`.

        Safety Hypothesis Status: SUPPORTED

        WARNING-EVOLUTION EVIDENCE ASSESSMENT
        Structured Warning-Evolution Evidence:
- matched: no
- matching method: Unavailable
- matched version: Unavailable
- matched child warning: Unavailable
- location threshold: 3
- later versions checked: Unavailable
- SCA reports checked: Unavailable
- original evolution state: Unavailable
- trace completeness: Unavailable
- evidence reliability: LOW

        Evolution Analysis:
        The disagreement only signals that this warning deserves deeper review. The preserved evolution artifact is weak, so the final resolution rests on the visible truncation and capacity evidence.

        CROSS-EVIDENCE RESOLUTION
        The safety hypothesis is stronger because the source string is visibly truncated to a bounded tail before the final copy. Without a remaining unbounded source, the defect hypothesis is not established.

        Final Label: FP
