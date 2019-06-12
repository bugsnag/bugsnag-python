# tweak these
TRIES=1000
#COMMAND="pyenv exec tox -e py35-flask"
COMMAND="nosetests --tests tests.test_utils"

# tweaked from http://unix.stackexchange.com/a/82602
n=0
until [ $n -ge $TRIES ]
do
  echo "****************************************************************************"
  echo "****************************************************************************"
  echo "ATTEMPT $n"
  echo "****************************************************************************"
  echo "****************************************************************************"
  $COMMAND || break
  n=$[$n+1]
done

echo Ended at attempt $n
