$(document).ready(function() {
  $('#people').DataTable({
    processing: true,
    serverSide: true,
    ajax: '/datatable',
    pageLength: 10,
    lengthMenu: [ [10,25,50,100], [10,25,50,100] ],
    columns: [
      { data: 'id' },
      { data: 'name' },
      { data: 'position' },
      { data: 'office' },
      { data: 'age' },
      { data: 'start_date' },
      { data: 'salary' }
    ]
  });
});
