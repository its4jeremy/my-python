const topicFilter = document.querySelector('#topic-filter');
const populatedOnly = document.querySelector('#populated-only');
if (topicFilter && populatedOnly) {
  const topics = [...document.querySelectorAll('[data-topic]')];
  const filter = () => {
    const query = topicFilter.value.trim().toLowerCase();
    let visible = 0;
    topics.forEach(topic => {
      topic.hidden = !topic.dataset.topic.toLowerCase().includes(query) ||
        (populatedOnly.checked && Number(topic.dataset.count) === 0);
      if (!topic.hidden) visible += 1;
    });
    document.querySelector('#filter-empty').hidden = visible !== 0;
  };
  topicFilter.addEventListener('input', filter);
  populatedOnly.addEventListener('change', filter);
}
