root = exports ? this

root.notify = (msg,status) ->
    humanMsg.displayMsg msg, status

root.setError = (field) ->
	$('#id_'+field).parent().parent().addClass('error')

root.setError = (field) ->
  $("#id_" + field).parent().parent().addClass "error"